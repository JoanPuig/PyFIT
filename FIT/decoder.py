# Copyright 2019 Joan Puig
# See LICENSE for details


import importlib
import warnings
from typing import Dict, Union, Optional, Tuple, Any
import sys

from FIT.base_types import UnsignedInt8, UnsignedInt16, UnsignedInt32, UnsignedInt64, BASE_TYPE_NUMBER_TO_CLASS
from FIT.model import MessageDefinition, File, FileHeader, Record, NormalRecordHeader, CompressedTimestampRecordHeader, FieldDefinition, Architecture, RecordField, MessageContent, Message, UndocumentedMessage, ManufacturerSpecificMessage, \
    UndocumentedMessageField, DeveloperMessageField

import numpy as np


class FITFileContentError(Exception):
    pass


class FITFileContentWarning(Warning):
    pass


class UnsupportedFITFeature(Exception):
    pass


class FITGeneratedCodeNotFoundError(Exception):
    pass


class CRCCalculator:
    CRC_TABLE = [
        UnsignedInt16(0x0000),
        UnsignedInt16(0xCC01),
        UnsignedInt16(0xD801),
        UnsignedInt16(0x1400),
        UnsignedInt16(0xF001),
        UnsignedInt16(0x3C00),
        UnsignedInt16(0x2800),
        UnsignedInt16(0xE401),
        UnsignedInt16(0xA001),
        UnsignedInt16(0x6C00),
        UnsignedInt16(0x7800),
        UnsignedInt16(0xB401),
        UnsignedInt16(0x5000),
        UnsignedInt16(0x9C01),
        UnsignedInt16(0x8801),
        UnsignedInt16(0x4400),
    ]

    x000F = UnsignedInt16(0x000F)
    x0FFF = UnsignedInt16(0x0FFF)

    def __init__(self):
        self.current = UnsignedInt16(0)

    def reset(self) -> None:
        self.current = UnsignedInt16(0)

    def new_byte(self, byte) -> None:
        crc = self.current

        tmp = CRCCalculator.CRC_TABLE[crc & CRCCalculator.x000F]  # tmp = crc_table[crc & 0xF];
        crc = (crc >> 4) & CRCCalculator.x0FFF  # crc = (crc >> 4) & 0x0FFF;
        crc = crc ^ tmp ^ CRCCalculator.CRC_TABLE[byte & CRCCalculator.x000F]  # crc = crc ^ tmp ^ crc_table[byte & 0xF];

        tmp = CRCCalculator.CRC_TABLE[crc & CRCCalculator.x000F]  # tmp = crc_table[crc & 0xF];
        crc = (crc >> 4) & CRCCalculator.x0FFF  # crc = (crc >> 4) & 0x0FFF;
        crc = crc ^ tmp ^ CRCCalculator.CRC_TABLE[(byte >> 4) & CRCCalculator.x000F]  # crc = crc ^ tmp ^ crc_table[(byte >> 4) & 0xF];

        self.current = crc


class ByteReader:
    bytes_read: int
    crc_calculator: CRCCalculator
    raw_bytes: Union[bytearray, bytes]

    def __init__(self, raw_bytes: bytes):
        self.bytes_read = 0
        self.raw_bytes = raw_bytes
        self.crc_calculator = CRCCalculator()

    def read_byte(self) -> UnsignedInt8:
        if self.bytes_left() == 0:
            raise FITFileContentError('Unexpected end of file encountered')

        byte = UnsignedInt8(self.raw_bytes[self.bytes_read])
        self.bytes_read = self.bytes_read + 1
        self.crc_calculator.new_byte(byte)
        return byte

    def read_double_byte(self) -> UnsignedInt16:
        return UnsignedInt16(np.array([self.read_byte() for _ in range(0, 2)]).view(UnsignedInt16)[0])

    def read_quad_byte(self) -> UnsignedInt32:
        return UnsignedInt32(np.array([self.read_byte() for _ in range(0, 4)]).view(UnsignedInt32)[0])

    def read_octo_byte(self) -> UnsignedInt32:
        return UnsignedInt64(np.array([self.read_byte() for _ in range(0, 8)]).view(UnsignedInt64)[0])

    def read_bytes(self, count: int) -> bytes:
        return bytes([self.read_byte() for _ in range(0, count)])

    def bytes_left(self):
        return len(self.raw_bytes) - self.bytes_read


class Decoder:
    TIMESTAMP_FIELD_NUMBER = 253
    MESSAGE_INDEX_FIELD_NUMBER = 254
    PART_INDEX_FIELD_NUMBER = 250

    IS_COMPRESSED_TIMESTAMP_HEADER_POSITION = 8 - 1
    IS_DEFINITION_MESSAGE_POSITION = 7 - 1
    HAS_DEVELOPER_DATA_POSITION = 6 - 1
    RESERVED_BIT_POSITION = 5 - 1

    reader: ByteReader
    most_recent_timestamp: Optional[UnsignedInt32]

    message_definitions: Dict[int, MessageDefinition]

    def __init__(self, reader: ByteReader):
        self.reader = reader
        self.message_definitions = {}
        self.most_recent_timestamp = None

    def decode_file(self) -> File:
        header = self.decode_file_header()
        records = self.decode_records(header.data_size)
        crc = self.decode_crc(False)

        return File(header, records, crc)

    def decode_file_header(self) -> FileHeader:
        header_size = self.reader.read_byte()
        protocol_version = self.reader.read_byte()
        profile_version = self.reader.read_double_byte()
        data_size = self.reader.read_quad_byte()
        data_type = ''.join([chr(self.reader.read_byte()) for _ in range(0, 4)])

        if header_size not in [12, 14]:
            raise FITFileContentError(f'Invalid header size, Expected: 12 or 14, read: {header_size}')

        if data_type != '.FIT':
            raise FITFileContentError(f'Invalid header text. Expected: ".FIT", read: "{data_type}"')

        if header_size == 14:
            crc = self.decode_crc(True)
        else:
            crc = None

        return FileHeader(header_size, protocol_version, profile_version, data_size, data_type, crc)

    def decode_records(self, data_size: UnsignedInt32) -> Tuple[Record]:
        initial_bytes_read = self.reader.bytes_read

        records = []
        while self.reader.bytes_read - initial_bytes_read < data_size:
            records.append(self.decode_record())

        return tuple(records)

    def decode_record(self) -> Record:
        header_byte = self.reader.read_byte()
        is_compressed_timestamp_header = Decoder.bit_get(header_byte, Decoder.IS_COMPRESSED_TIMESTAMP_HEADER_POSITION)

        if is_compressed_timestamp_header:
            header = self.decode_compressed_timestamp_record_header(header_byte)
        else:
            header = self.decode_normal_record_header(header_byte)

        if header.is_definition_message:
            content = self.decode_message_definition(header)
        else:
            content = self.decode_message_content(header)

        return Record(header, content)

    def decode_normal_record_header(self, header: UnsignedInt8) -> NormalRecordHeader:
        is_definition_message = Decoder.bit_get(header, Decoder.IS_DEFINITION_MESSAGE_POSITION)
        has_developer_data = Decoder.bit_get(header, Decoder.HAS_DEVELOPER_DATA_POSITION)
        reserved_bit = Decoder.bit_get(header, Decoder.RESERVED_BIT_POSITION)

        if reserved_bit:
            raise FITFileContentError('Reserved bit on record header is 1, expected 0')

        local_message_type = header & UnsignedInt8(15)  # 1st to 4th bits

        return NormalRecordHeader(True, is_definition_message, has_developer_data, local_message_type)

    def decode_compressed_timestamp_record_header(self, header_byte: UnsignedInt8) -> CompressedTimestampRecordHeader:
        local_message_type = (header_byte >> 5) & 0x3  # 5th to 7th bits
        time_offset = header_byte & 0x1F  # 1st to 4th bits
        return CompressedTimestampRecordHeader(False, False, False, local_message_type, time_offset, self.most_recent_timestamp)

    def decode_field_definition(self) -> FieldDefinition:
        number = self.reader.read_byte()
        size = self.reader.read_byte()
        type_byte = self.reader.read_byte()
        endian_ability = Decoder.bit_get(type_byte, 8 - 1)
        base_type = type_byte & UnsignedInt8(31)  # 1st to 5th bits
        reserved_bits = type_byte & UnsignedInt8(96)  # 6th to 7th bits

        if reserved_bits:
            raise FITFileContentError(f'Invalid FieldDefinition reserved bits, expected 0, read {reserved_bits}')

        return FieldDefinition(number, size, endian_ability, base_type)

    def decode_message_definition(self, header: NormalRecordHeader) -> MessageDefinition:
        reserved_byte = self.reader.read_byte()

        if reserved_byte:
            raise FITFileContentError('Reserved byte after record header is not 0')

        architecture = Architecture(self.reader.read_byte())
        global_message_number = UnsignedInt16.from_bytes(self.reader.read_bytes(2))

        number_of_fields = self.reader.read_byte()
        field_definitions = tuple([self.decode_field_definition() for _ in range(0, number_of_fields)])

        number_of_developer_fields = self.reader.read_byte() if header.has_developer_data else 0
        developer_field_definitions = tuple([self.decode_field_definition() for _ in range(0, number_of_developer_fields)])

        definition = MessageDefinition(reserved_byte, architecture, global_message_number, field_definitions, developer_field_definitions)
        self.message_definitions[header.local_message_type] = definition
        return definition

    def decode_field(self, field_definition: FieldDefinition) -> RecordField:
        raw_bytes = self.reader.read_bytes(field_definition.size)  # TODO endianness

        type_class = BASE_TYPE_NUMBER_TO_CLASS[field_definition.base_type]
        decoded_value = type_class.from_bytes(raw_bytes)

        if field_definition.number == Decoder.MESSAGE_INDEX_FIELD_NUMBER:
            if field_definition.base_type != UnsignedInt16.metadata().base_type_number:
                raise FITFileContentError('Message Index field number {} is expected to be of type {}, {} found', Decoder.MESSAGE_INDEX_FIELD_NUMBER, UnsignedInt16.__name__, type_class.__name__)

        if field_definition.number == Decoder.PART_INDEX_FIELD_NUMBER:
            if field_definition.base_type != UnsignedInt32.metadata().base_type_number:
                raise FITFileContentError('Part Index field number {} is expected to be of type {}, {} found', Decoder.MESSAGE_INDEX_FIELD_NUMBER, UnsignedInt32.__name__, type_class.__name__)

        if field_definition.number == Decoder.TIMESTAMP_FIELD_NUMBER:
            if field_definition.base_type != UnsignedInt32.metadata().base_type_number:
                raise FITFileContentError('Timestamp field number {} is expected to be of type {}, {} found', Decoder.TIMESTAMP_FIELD_NUMBER, UnsignedInt32.__name__, type_class.__name__)
            self.most_recent_timestamp = decoded_value

        return RecordField(decoded_value)

    def decode_message_content(self, header: NormalRecordHeader) -> MessageContent:
        message_definition = self.message_definitions.get(header.local_message_type)

        if not message_definition:
            raise FITFileContentError(f'Unable to find local message type definition {header.local_message_type}')

        fields = tuple([self.decode_field(field_definition) for field_definition in message_definition.field_definitions])
        developer_fields = tuple([self.decode_field(developer_field_definition) for developer_field_definition in message_definition.developer_field_definitions])
        return MessageContent(fields, developer_fields)

    def decode_crc(self, allow_zero) -> UnsignedInt16:
        computed_crc = self.reader.crc_calculator.current
        expected_crc = self.reader.read_double_byte()

        self.reader.crc_calculator.reset()

        if allow_zero and expected_crc == UnsignedInt16(0):
            return expected_crc

        if computed_crc != expected_crc:
            raise FITFileContentError(f'Invalid CRC. Expected: {expected_crc}, computed: {computed_crc}')

        return expected_crc

    @staticmethod
    def bit_get(byte: UnsignedInt8, position: int) -> bool:
        return byte & (1 << position) > 0

    @staticmethod
    def decode_fit_file(file_name: str) -> File:
        # Reads the binary data of the .FIT file
        file_bytes = open(file_name, "rb").read()

        # Constructs a ByteReader and Decoder object
        byte_reader = ByteReader(file_bytes)
        decoder = Decoder(byte_reader)

        # Decodes the file
        return decoder.decode_file()

    @staticmethod
    def decode_fit_messages(file_name: str, error_on_undocumented_message: bool = False, error_on_undocumented_field: bool = False, error_on_invalid_enum_value: bool = False) -> Tuple[Message]:
        # Reads the FIT file
        file = Decoder.decode_fit_file(file_name)

        try:
            from FIT.types import MesgNum
        except ModuleNotFoundError:
            raise FITGeneratedCodeNotFoundError('Unable to load FIT.types, make sure you have generated the code first')

        messages = []
        definitions = {}
        warned_undocumented_msg_num = []
        warned_manufacturer_specific_messages = []
        warned_undocumented_fields = []
        for record in file.records:
            if isinstance(record.content, MessageDefinition):
                definitions[record.header.local_message_type] = record.content
                global_message_number = record.content.global_message_number
                if global_message_number not in MesgNum._value2member_map_:
                    is_manufacturer_specific = MesgNum.MfgRangeMin.value <= global_message_number <= MesgNum.MfgRangeMax.value
                    if is_manufacturer_specific:
                        warning_message = f'DefinitionMessage references MesgNum {global_message_number} which is manufacturer specific'
                        if warning_message not in warned_manufacturer_specific_messages:
                            warnings.warn(warning_message, FITFileContentWarning)
                            warned_manufacturer_specific_messages.append(warning_message)
                    else:
                        error_message = f'DefinitionMessage references MesgNum {global_message_number} which is not documented'
                        if error_on_undocumented_message:
                            raise FITFileContentError(error_message)
                        else:
                            if error_message not in warned_undocumented_msg_num:
                                warnings.warn(error_message, FITFileContentWarning)
                                warned_undocumented_msg_num.append(error_message)

            elif isinstance(record.content, MessageContent):
                local_message_type = record.header.local_message_type

                if local_message_type not in definitions:
                    raise FITFileContentError(f'Local message type {local_message_type} has not been previously defined')

                message_definition = definitions[local_message_type]

                is_manufacturer_specific = MesgNum.MfgRangeMin.value <= message_definition.global_message_number <= MesgNum.MfgRangeMax.value
                if is_manufacturer_specific:
                    message_class = ManufacturerSpecificMessage  # TODO custom manufacturer specific messages
                    class_name = ManufacturerSpecificMessage.__name__
                else:
                    if message_definition.global_message_number in MesgNum._value2member_map_:
                        global_message_number = MesgNum(message_definition.global_message_number)
                        mod = importlib.import_module('FIT.messages')
                        message_class = getattr(mod, global_message_number.name)
                        class_name = global_message_number.name
                    else:
                        message_class = UndocumentedMessage
                        class_name = UndocumentedMessage.__name__

                developer_fields = Decoder.extract_developer_fields(record, message_definition, error_on_invalid_enum_value)
                expected_field_numbers = message_class.expected_field_numbers()
                undocumented_fields = Decoder.extract_undocumented_fields(record.content, message_definition, expected_field_numbers, error_on_invalid_enum_value)
                fields = Decoder.extract_fields(record.content, message_definition, expected_field_numbers)
                message = message_class.from_extracted_fields(fields, developer_fields, undocumented_fields, error_on_invalid_enum_value)

                for undocumented_field in message.undocumented_fields:
                    error_message = f'{class_name} message has undocumented field number {undocumented_field.definition.number}'

                    if error_on_undocumented_field:
                        raise FITFileContentError(error_message)
                    else:
                        if error_message not in warned_undocumented_fields:
                            warnings.warn(error_message, FITFileContentWarning)
                            warned_undocumented_fields.append(error_message)

                messages.append(message)
            else:
                raise FITFileContentError(f'Unexpected record type: {type(record)}')

        return tuple(messages)

    @staticmethod
    def extract_developer_fields(record: Record, message_definition: MessageDefinition, error_on_invalid_enum_value: bool = True) -> Tuple[DeveloperMessageField]:
        developer_fields = []
        for developer_field in record.content.developer_fields:
            pass  # TODO developer fields from record
        return tuple(developer_fields)

    @staticmethod
    def extract_undocumented_fields(content: MessageContent, definition: MessageDefinition, expected_field_numbers: Tuple[int] = (), error_on_invalid_enum_value: bool = True) -> Tuple[UndocumentedMessageField]:
        undocumented = []
        for field_id, (field_position, field_definition) in definition.mapped_field_definitions().items():
            if field_id not in expected_field_numbers:
                undocumented.append(UndocumentedMessageField(field_definition, content.fields[field_position].value))

        return tuple(undocumented)

    @staticmethod
    def extract_fields(content: MessageContent, definition: MessageDefinition, expected_field_numbers: Tuple[int]) -> Dict[UnsignedInt8, Any]:
        # TODO compressed timestamp
        extracted_fields = {}
        field_number_to_index_map = definition.mapped_field_definitions()
        for field_number in expected_field_numbers:
            if field_number in field_number_to_index_map:
                extracted_fields[field_number] = content.fields[field_number_to_index_map[field_number][0]].value
            else:
                extracted_fields[field_number] = None

        return extracted_fields

    @staticmethod
    def cast_value(value, new_type, error_on_invalid_enum_value: bool):
        if value is None:
            return None
        if isinstance(value, tuple):
            return tuple(Decoder.cast_value(v, new_type, error_on_invalid_enum_value) for v in value)

        try:
            casted = new_type(value)
        except ValueError:
            if error_on_invalid_enum_value:
                raise sys.exc_info()[1]
            else:
                casted = new_type.Invalid

        return casted


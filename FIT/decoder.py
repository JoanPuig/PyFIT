# Copyright 2019 Joan Puig
# See LICENSE for details


from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Union

from FIT.base_types import UnsignedInt8, UnsignedInt16, UnsignedInt32, UnsignedInt64

import numpy as np


def parse_UnsignedInt16(hex_str: str) -> UnsignedInt16:
    return UnsignedInt16(int(hex_str, 16))


def bit_get(byte: UnsignedInt8, position: int) -> bool:
    return byte & (1 << position) > 0


class FITFileFormatError(Exception):
    pass


class UnsupportedFITFeature(Exception):
    pass


class CRCCalculator:
    CRC_TABLE = [
        parse_UnsignedInt16('0000'),
        parse_UnsignedInt16('CC01'),
        parse_UnsignedInt16('D801'),
        parse_UnsignedInt16('1400'),
        parse_UnsignedInt16('F001'),
        parse_UnsignedInt16('3C00'),
        parse_UnsignedInt16('2800'),
        parse_UnsignedInt16('E401'),
        parse_UnsignedInt16('A001'),
        parse_UnsignedInt16('6C00'),
        parse_UnsignedInt16('7800'),
        parse_UnsignedInt16('B401'),
        parse_UnsignedInt16('5000'),
        parse_UnsignedInt16('9C01'),
        parse_UnsignedInt16('8801'),
        parse_UnsignedInt16('4400'),
    ]

    x000F = parse_UnsignedInt16('000F')
    x0FFF = parse_UnsignedInt16('0FFF')

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

    def __init__(self, raw_bytes: Union[bytearray, bytes]):
        self.bytes_read = 0
        self.raw_bytes = raw_bytes
        self.crc_calculator = CRCCalculator()

    def read_byte(self) -> UnsignedInt8:
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

    def bytes_left(self):
        return len(self.raw_bytes) - self.bytes_read


class Architecture(Enum):
    LittleEndian = UnsignedInt8(0)
    BigEndian = UnsignedInt8(1)


@dataclass
class RecordHeader:
    pass


@dataclass
class NormalRecordHeader(RecordHeader):
    is_normal_header: bool
    is_definition_message: bool
    has_developer_data: bool
    reserved_bit: bool
    local_message_type: UnsignedInt8


@dataclass
class RecordContent:
    pass


@dataclass
class Field:
    bytes: bytearray


@dataclass
class FieldDefinition:
    number: UnsignedInt8
    size: UnsignedInt8
    endian_ability: bool
    base_type: UnsignedInt8
    reserved_bits: UnsignedInt8


@dataclass
class DeveloperField:
    pass


@dataclass
class DeveloperFieldDefinition:
    pass


@dataclass
class MessageDefinition(RecordContent):
    reserved_byte: UnsignedInt8
    architecture: Architecture
    global_message_number: UnsignedInt16
    field_definitions: List[FieldDefinition]
    developer_field_definitions: List[FieldDefinition]


@dataclass
class MessageContent(RecordContent):
    fields: List[Field]
    developer_fields: List[Field]


@dataclass
class Record:
    header: RecordHeader
    content: RecordContent


@dataclass
class FileHeader:
    header_size: UnsignedInt8
    protocol_version: UnsignedInt8
    profile_version: UnsignedInt16
    data_size: UnsignedInt32
    data_type: str
    crc: UnsignedInt16


@dataclass
class File:
    header: FileHeader
    records: List[Record]
    crc: UnsignedInt16


class Decoder:
    IS_NORMAL_HEADER_POSITION = 8-1
    IS_DEFINITION_MESSAGE_POSITION = 7-1
    HAS_DEVELOPER_DATA_POSITION = 6-1
    RESERVED_BIT_POSITION = 5-1

    reader: ByteReader

    message_definitions: Dict[int, MessageDefinition]

    def __init__(self, reader: ByteReader):
        self.reader = reader
        self.message_definitions = {}

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
            raise FITFileFormatError('Invalid header size, Expected: 12 or 14, read: {}'.format(header_size))

        if data_type != '.FIT':
            raise FITFileFormatError('Invalid header text. Expected: ".FIT", read: "{}}"'.format(data_type))

        if header_size == 14:
            crc = self.decode_crc(True)
        else:
            crc = None

        return FileHeader(header_size, protocol_version, profile_version, data_size, data_type, crc)

    def decode_records(self, data_size: UnsignedInt32) -> List[Record]:
        initial_bytes_read = self.reader.bytes_read

        records = []
        while self.reader.bytes_read - initial_bytes_read < data_size:
            records.append(self.decode_record())

        return records

    def decode_record(self) -> Record:
        header_byte = self.reader.read_byte()
        is_normal_header = not bit_get(header_byte, Decoder.IS_NORMAL_HEADER_POSITION)

        if is_normal_header:
            return self.decode_record_with_normal_header(header_byte)
        else:
            return self.decode_record_with_compressed_timestamp_header(header_byte)

    def decode_normal_record_header(self, header: UnsignedInt8) -> NormalRecordHeader:
        is_definition_message = bit_get(header, Decoder.IS_DEFINITION_MESSAGE_POSITION)
        has_developer_data = bit_get(header, Decoder.HAS_DEVELOPER_DATA_POSITION)
        reserved_bit = bit_get(header, Decoder.RESERVED_BIT_POSITION)

        if reserved_bit:
            raise FITFileFormatError('Reserved bit on record header is 1, expected 0')

        local_message_type = header & UnsignedInt8(15)  # 1st to 4th bits

        return NormalRecordHeader(True, is_definition_message, has_developer_data, reserved_bit, local_message_type)

    def decode_field_definition(self) -> FieldDefinition:
        number = self.reader.read_byte()
        size = self.reader.read_byte()
        type_byte = self.reader.read_byte()
        endian_ability = bit_get(type_byte, 8-1)
        base_type = type_byte & UnsignedInt8(31)  # 1st to 5th bits
        reserved_bits = type_byte & UnsignedInt8(96)  # 6th to 7th bits

        if reserved_bits:
            raise FITFileFormatError('Invalid FieldDefinition reserved bits, expected 0, read {}'.format(reserved_bits))

        return FieldDefinition(number, size, endian_ability, base_type, reserved_bits)

    def decode_message_definition(self, header: NormalRecordHeader) -> MessageDefinition:
        reserved_byte = self.reader.read_byte()

        if reserved_byte:
            raise FITFileFormatError('Reserved byte after record header is not 0')

        architecture = Architecture(self.reader.read_byte())
        global_message_number = self.reader.read_double_byte()

        number_of_fields = self.reader.read_byte()
        field_definitions = [self.decode_field_definition() for _ in range(0, number_of_fields)]

        number_of_developer_fields = self.reader.read_byte() if header.has_developer_data else 0
        developer_field_definitions = [self.decode_field_definition() for _ in range(0, number_of_developer_fields)]

        definition = MessageDefinition(reserved_byte, architecture, global_message_number, field_definitions, developer_field_definitions)
        self.message_definitions[header.local_message_type] = definition
        return definition

    def decode_field(self, field_definition: FieldDefinition) -> Field:
        raw_bytes = [self.reader.read_byte() for _ in range(0, field_definition.size)]
        return Field(bytearray(raw_bytes))

    def decode_message_content(self, header: NormalRecordHeader) -> MessageContent:
        message_definition = self.message_definitions.get(header.local_message_type)

        if not message_definition:
            raise FITFileFormatError('Unable to find local message type definition {}'.format(header.local_message_type))

        fields = [self.decode_field(field_definition) for field_definition in message_definition.field_definitions]
        developer_fields = [self.decode_field(developer_field_definition) for developer_field_definition in message_definition.developer_field_definitions]
        return MessageContent(fields, developer_fields)

    def decode_record_with_normal_header(self, header) -> Record:
        header = self.decode_normal_record_header(header)

        if header.is_definition_message:
            content = self.decode_message_definition(header)
        else:
            content = self.decode_message_content(header)

        return Record(header, content)

    def decode_record_with_compressed_timestamp_header(self, header) -> Record:
        raise UnsupportedFITFeature('Compressed timestamp records are not supported')

    def decode_crc(self, allow_zero) -> UnsignedInt16:
        computed_crc = self.reader.crc_calculator.current
        expected_crc = self.reader.read_double_byte()

        self.reader.crc_calculator.reset()

        if allow_zero and expected_crc == UnsignedInt16(0):
            return expected_crc

        if computed_crc != expected_crc:
            raise FITFileFormatError('Invalid CRC. Expected: {}, computed: {}'.format(expected_crc, computed_crc))

        return expected_crc

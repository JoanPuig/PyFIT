# Copyright 2019 Joan Puig
# See LICENSE for details
import functools
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Dict

from FIT.base_types import BaseType, UnsignedInt8, UnsignedInt16, UnsignedInt32


class Architecture(Enum):
    LittleEndian = UnsignedInt8(0)
    BigEndian = UnsignedInt8(1)


@dataclass(frozen=True)
class RecordHeader:
    is_normal_header: bool
    is_definition_message: bool
    has_developer_data: bool
    local_message_type: UnsignedInt8


@dataclass(frozen=True)
class NormalRecordHeader(RecordHeader):
    pass


@dataclass(frozen=True)
class CompressedTimestampRecordHeader(RecordHeader):
    time_offset: UnsignedInt8
    previous_Timestamp: UnsignedInt32


@dataclass(frozen=True)
class RecordContent:
    pass


@dataclass(frozen=True)
class RecordField:
    value: BaseType


@dataclass(frozen=True)
class FieldDefinition:
    number: UnsignedInt8
    size: UnsignedInt8
    endian_ability: bool
    base_type: UnsignedInt8
    reserved_bits: UnsignedInt8


@dataclass(frozen=True)
class MessageDefinition(RecordContent):
    reserved_byte: UnsignedInt8
    architecture: Architecture
    global_message_number: UnsignedInt16
    field_definitions: Tuple[FieldDefinition]
    developer_field_definitions: Tuple[FieldDefinition]

    @functools.lru_cache(1)
    def mapped_field_definitions(self) -> Dict[UnsignedInt8, Tuple[int, FieldDefinition]]:
        return {definition.number: (i, definition) for i, definition in enumerate(self.field_definitions)}

    @functools.lru_cache(1)
    def mapped_developer_field_definitions(self) -> Dict[UnsignedInt8, Tuple[int, FieldDefinition]]:
        return {definition.number: (i, definition) for i, definition in enumerate(self.developer_field_definitions)}

    def field_definition(self, number: UnsignedInt8) -> Tuple[int, FieldDefinition]:
        return self.mapped_field_definitions()[number]

    def developer_field_definition(self, number: UnsignedInt8) -> Tuple[int, FieldDefinition]:
        return self.mapped_developer_field_definitions()[number]


@dataclass(frozen=True)
class MessageContent(RecordContent):
    fields: Tuple[RecordField]
    developer_fields: Tuple[RecordField]


@dataclass(frozen=True)
class Record:
    header: RecordHeader
    content: RecordContent


@dataclass(frozen=True)
class FileHeader:
    header_size: UnsignedInt8
    protocol_version: UnsignedInt8
    profile_version: UnsignedInt16
    data_size: UnsignedInt32
    data_type: str
    crc: UnsignedInt16


@dataclass(frozen=True)
class File:
    header: FileHeader
    records: Tuple[Record]
    crc: UnsignedInt16


@dataclass(frozen=True)
class DeveloperMessageField:
    definition: FieldDefinition
    value: BaseType


@dataclass(frozen=True)
class UndocumentedMessageField:
    definition: FieldDefinition
    value: BaseType


@dataclass(frozen=True)
class Message:
    developer_fields: Tuple[DeveloperMessageField]
    undocumented_fields: Tuple[UndocumentedMessageField]

    @staticmethod
    def developer_fields_from_record(record: Record, message_definition: MessageDefinition) -> Tuple[DeveloperMessageField]:
        if record.content.developer_fields:
            return []
        else:
            return []

    @staticmethod
    def undocumented_fields_from_record(content: MessageContent, definition: MessageDefinition, expected_fields: Tuple[int]) -> Tuple[UndocumentedMessageField]:
        undocumented = []
        for field_id, (field_position, field_definition) in definition.mapped_field_definitions().items():
            if field_id not in expected_fields:
                undocumented.append(UndocumentedMessageField(field_definition, content.fields[field_position].value))

        return tuple(undocumented)


@dataclass(frozen=True)
class ManufacturerSpecificMessage(Message):
    @staticmethod
    def from_record(record: Record, message_definition: MessageDefinition):
        developer_fields = Message.developer_fields_from_record(record, message_definition)
        undocumented_fields = Message.undocumented_fields_from_record(record, message_definition)
        return ManufacturerSpecificMessage(developer_fields, undocumented_fields)


@dataclass(frozen=True)
class UndocumentedMessage(Message):
    @staticmethod
    def from_record(record: Record, message_definition: MessageDefinition):
        developer_fields = []
        undocumented_fields = []  # TODO all fields are undocumented Message.undocumented_fields_from_record(record, message_definition)
        return UndocumentedMessage(developer_fields, undocumented_fields)


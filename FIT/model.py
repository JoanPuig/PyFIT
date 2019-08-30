# Copyright 2019 Joan Puig
# See LICENSE for details


from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import List

from FIT.base_types import BaseType, UnsignedInt8, UnsignedInt16, UnsignedInt32


class Architecture(Enum):
    LittleEndian = UnsignedInt8(0)
    BigEndian = UnsignedInt8(1)


@dataclass
class RecordHeader:
    is_normal_header: bool
    is_definition_message: bool
    has_developer_data: bool
    local_message_type: UnsignedInt8


@dataclass
class NormalRecordHeader(RecordHeader):
    pass


@dataclass
class CompressedTimestampRecordHeader(RecordHeader):
    time_offset: UnsignedInt8
    previous_Timestamp: UnsignedInt32


@dataclass
class RecordContent:
    pass


@dataclass
class RecordField:
    value: BaseType


@dataclass
class FieldDefinition:
    number: UnsignedInt8
    size: UnsignedInt8
    endian_ability: bool
    base_type: UnsignedInt8
    reserved_bits: UnsignedInt8


@dataclass
class MessageDefinition(RecordContent):
    reserved_byte: UnsignedInt8
    architecture: Architecture
    global_message_number: UnsignedInt16
    field_definitions: List[FieldDefinition]
    developer_field_definitions: List[FieldDefinition]


@dataclass
class MessageContent(RecordContent):
    fields: List[RecordField]
    developer_fields: List[RecordField]


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


@dataclass
class DeveloperMessageField:
    definition: FieldDefinition
    value: BaseType


@dataclass
class UndocumentedMessageField:
    definition: FieldDefinition
    value: BaseType


@dataclass
class Message(ABC):
    developer_fields: List[DeveloperMessageField]
    undocumented_fields: List[UndocumentedMessageField]


@dataclass
class UndocumentedMessage(Message):
    @staticmethod
    def from_record(record: Record):
        return UndocumentedMessage(None, None)


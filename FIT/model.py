# Copyright 2019 Joan Puig
# See LICENSE for details


import functools

from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Dict, Union

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

    def _xstr_(self):
        last_fields = ['developer_fields', 'undocumented_fields']
        new_last_fields = []
        fields = list(self.__dataclass_fields__.keys())
        for last_field in last_fields:
            if last_field in fields:
                fields.remove(last_field)
                new_last_fields.append(last_field)

        field_strs = []
        for k in fields:
            field_val = self.__dict__[k]
            if field_val is not None:
                if isinstance(field_val, tuple):
                    if len(field_val) == 0:
                        continue
                field_strs.append(k + '=' + str(field_val))
        fields_str = ", ".join(field_strs)
        if self.undocumented_fields is not None and len(self.undocumented_fields) > 0:
            undocumented_field_strs = ''
            undocumented_fields_str = f'undocumented_fields=[{", ".join([undocumented_field_str for undocumented_field_str in undocumented_field_strs])}]'
            if len(fields_str) >= 0:
                fields_str = fields_str + undocumented_fields_str
            else:
                fields_str = undocumented_fields_str



        return f'{type(self).__name__}({fields_str})'


@dataclass(frozen=True)
class ManufacturerSpecificMessage(Message):
    @staticmethod
    def expected_field_numbers() -> Tuple[int]:
        return ()

    @staticmethod
    def from_extracted_fields(extracted_fields, developer_fields: Tuple[DeveloperMessageField], undocumented_fields: Tuple[UndocumentedMessageField], error_on_invalid_enum_value: bool) -> "ManufacturerSpecificMessage":
        return ManufacturerSpecificMessage(developer_fields, undocumented_fields)


@dataclass(frozen=True)
class UndocumentedMessage(Message):
    @staticmethod
    def expected_field_numbers() -> Tuple[int]:
        return ()

    @staticmethod
    def from_extracted_fields(extracted_fields, developer_fields: Tuple[DeveloperMessageField], undocumented_fields: Tuple[UndocumentedMessageField], error_on_invalid_enum_value: bool) -> "UndocumentedMessage":
        return UndocumentedMessage(developer_fields, undocumented_fields)


@dataclass(frozen=True)
class FieldMetadata:
    name: str
    type: str
    #array: str
    #components: str
    scale: int
    offset: int
    units: str
    #bits: int
    #accumulated: Union[str, int]


@dataclass(frozen=True)
class DynamicFieldMetadata(FieldMetadata):
    ref_field_name: str
    ref_field_value: str


@dataclass(frozen=True)
class NormalFieldMetadata(FieldMetadata):
    number: int


@dataclass(frozen=True)
class MessageMetadata:
    fields_metadata: Tuple[FieldMetadata]

    @functools.lru_cache(1)
    def field_numbers(self) -> Tuple[int]:
        return tuple([field_metadata.number for field_metadata in self.fields_metadata if isinstance(field_metadata, NormalFieldMetadata)])

    @functools.lru_cache(1)
    def field_names(self) -> Tuple[str]:
        return tuple([field_metadata.name for field_metadata in self.fields_metadata])


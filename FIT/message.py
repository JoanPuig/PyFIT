# Copyright 2019 Joan Puig
# See LICENSE for details


from abc import ABC
from dataclasses import dataclass
from typing import List

from FIT.base_types import BaseType
from FIT.decoder import FieldDefinition, Record, File


@dataclass
class DeveloperField:
    definition: FieldDefinition
    definition_record: Record
    content: BaseType


@dataclass
class UndocumentedField:
    definition: FieldDefinition
    content: Record


@dataclass
class Message(ABC):
    content: Record
    developer_fields: List[DeveloperField]
    undocumented_fields: List[UndocumentedField]


# Copyright 2019 Joan Puig
# See LICENSE for details


from abc import ABC
from dataclasses import dataclass

import numpy as np


@dataclass
class TypeMetadata:
    base_type: int
    endian_ability: bool
    base_type_field: int
    invalid_value: int
    underlying_bytes: int


class BaseType(ABC):
    pass


class Enum(np.uint8, BaseType):
    metadata = TypeMetadata(0, False, int('0x00', 16), int('0xFF', 16), 1)


class SingedInt8(np.int8, BaseType):
    metadata = TypeMetadata(1, False, int('0x01', 16), int('0x7F', 16), 1)


class UnsignedInt8(np.uint8, BaseType):
    metadata = TypeMetadata(2, False, int('0x02', 16), int('0xFF', 16), 1)


class SignedInt16(np.int16, BaseType):
    metadata = TypeMetadata(3, True, int('0x83', 16), int('0x7FFF', 16), 2)


class UnsignedInt16(np.uint16, BaseType):
    metadata = TypeMetadata(4, True, int('0x84', 16), int('0xFFFF', 16), 2)


class SignedInt32(np.int32, BaseType):
    metadata = TypeMetadata(5, True, int('0x85', 16), int('0x7FFFFFFF', 16), 4)


class UnsignedInt32(np.uint32, BaseType):
    metadata = TypeMetadata(6, True, int('0x86', 16), int('0xFFFFFFFF', 16), 4)


class String(str, BaseType):
    metadata = TypeMetadata(7, False, int('0x07', 16), int('0x00', 16), 1)


class Float32(np.float32, BaseType):
    metadata = TypeMetadata(8, True, int('0x88', 16), int('0xFFFFFFFF', 16), 4)


class Float64(np.float64, BaseType):
    metadata = TypeMetadata(9, True, int('0x89', 16), int('0xFFFFFFFFFFFFFFFF', 16), 8)


class UnsignedInt8z(np.uint8, BaseType):
    metadata = TypeMetadata(10, False, int('0x0A', 16), int('0x00', 16), 1)


class UnsignedInt16z(np.uint16, BaseType):
    metadata = TypeMetadata(11, True, int('0x8B', 16), int('0x0000', 16), 2)


class UnsignedInt32z(np.uint32, BaseType):
    metadata = TypeMetadata(12, True, int('0x8C', 16), int('0x00000000', 16), 4)


class Bool(np.uint8, BaseType):
    metadata = TypeMetadata(13, False, int('0x0D', 16), int('0xFF', 16), 1)


class Byte(np.uint8, BaseType):
    metadata = TypeMetadata(13, False, int('0x0D', 16), int('0xFF', 16), 1)


class SignedInt64(np.int64, BaseType):
    metadata = TypeMetadata(14, True, int('0x8E', 16), int('0x7FFFFFFFFFFFFFFF', 16), 8)


class UnsignedInt64(np.uint64, BaseType):
    metadata = TypeMetadata(15, True, int('0x8F', 16), int('0xFFFFFFFFFFFFFFFF', 16), 8)


class UnsignedInt64z(np.uint64, BaseType):
    metadata = TypeMetadata(16, True, int('0x90', 16), int('0x0000000000000000', 16), 8)

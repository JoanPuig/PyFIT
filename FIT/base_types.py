# Copyright 2019 Joan Puig
# See LICENSE for details


from abc import ABC
from dataclasses import dataclass
import numpy as np


BASE_TYPE_NAME_MAP = {
    'sint8': 'SignedInt8',
    'sint16': 'SignedInt16',
    'sint32': 'SignedInt32',
    'sint64': 'SignedInt64',
    'uint8': 'UnsignedInt8',
    'uint16': 'UnsignedInt16',
    'uint32': 'UnsignedInt32',
    'unit64': 'UnsignedInt64',
    'uint8z': 'UnsignedInt8z',
    'uint16z': 'UnsignedInt16z',
    'uint32z': 'UnsignedInt32z',
    'uint64z': 'UnsignedInt64z',
    'enum': 'FITEnum',
    'string': 'String',
    'float32': 'Float32',
    'float64': 'Float64',
    'byte': 'Byte',
    'bool': 'Bool'
}


@dataclass
class TypeMetadata:
    base_type_number: int
    endian_ability: bool
    base_type_field: int
    invalid_value: int
    underlying_bytes: int
    fit_name: str
    numpy_type: type


class BaseType(ABC):
    pass


class FITValueDecodingError(Exception):
    pass


def from_bytes(c, raw_bytes: bytes):
    if (len(raw_bytes) % c.metadata.underlying_bytes) != 0:
        raise FITValueDecodingError('{} expected to be multiple of {} bytes, {} received', BASE_TYPE_NAME_MAP[c.metadata.fit_name], c.metadata.underlying_bytes, len(raw_bytes))

    array = np.frombuffer(raw_bytes, dtype=c.metadata.numpy_type)

    if len(array) == 1:
        return c(array[0])
    else:
        return [c(v) for v in array.tolist()]


class FITEnum(np.uint8, BaseType):
    metadata = TypeMetadata(0, False, int('0x00', 16), int('0xFF', 16), 1, 'enum', np.uint8)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(FITEnum, raw_bytes)


class UnsignedInt8(np.uint8, BaseType):
    metadata = TypeMetadata(2, False, int('0x02', 16), int('0xFF', 16), 1, 'uint8', np.uint8)

    @staticmethod
    def from_bytes(raw_bytes: bytes):  # TODO: type check [UnsignedInt8]
        return from_bytes(UnsignedInt8, raw_bytes)


class SignedInt8(np.int8, BaseType):
    metadata = TypeMetadata(1, False, int('0x01', 16), int('0x7F', 16), 1, 'sint8', np.int8)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(SignedInt8, raw_bytes)


class SignedInt16(np.int16, BaseType):
    metadata = TypeMetadata(3, True, int('0x83', 16), int('0x7FFF', 16), 2, 'sint16', np.int16)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(SignedInt16, raw_bytes)


class UnsignedInt16(np.uint16, BaseType):
    metadata = TypeMetadata(4, True, int('0x84', 16), int('0xFFFF', 16), 2, 'uint16', np.uint16)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(UnsignedInt16, raw_bytes)


class SignedInt32(np.int32, BaseType):
    metadata = TypeMetadata(5, True, int('0x85', 16), int('0x7FFFFFFF', 16), 4, 'sint32', np.int32)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(SignedInt32, raw_bytes)


class UnsignedInt32(np.uint32, BaseType):
    metadata = TypeMetadata(6, True, int('0x86', 16), int('0xFFFFFFFF', 16), 4, 'uint32', np.uint32)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(UnsignedInt32, raw_bytes)


class String(str, BaseType):
    metadata = TypeMetadata(7, False, int('0x07', 16), int('0x00', 16), 1, 'string', str)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return String(raw_bytes)


class Float32(np.float32, BaseType):
    metadata = TypeMetadata(8, True, int('0x88', 16), int('0xFFFFFFFF', 16), 4, 'float32', np.float32)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(Float32, raw_bytes)


class Float64(np.float64, BaseType):
    metadata = TypeMetadata(9, True, int('0x89', 16), int('0xFFFFFFFFFFFFFFFF', 16), 8, 'float64', np.float64)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(Float64, raw_bytes)


class UnsignedInt8z(np.uint8, BaseType):
    metadata = TypeMetadata(10, False, int('0x0A', 16), int('0x00', 16), 1, 'uint8z', np.uint8)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(UnsignedInt8z, raw_bytes)


class UnsignedInt16z(np.uint16, BaseType):
    metadata = TypeMetadata(11, True, int('0x8B', 16), int('0x0000', 16), 2, 'uint16z', np.uint16)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(UnsignedInt16z, raw_bytes)


class UnsignedInt32z(np.uint32, BaseType):
    metadata = TypeMetadata(12, True, int('0x8C', 16), int('0x00000000', 16), 4, 'uint32z', np.uint32)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(UnsignedInt32z, raw_bytes)


class Byte(np.uint8, BaseType):
    metadata = TypeMetadata(13, False, int('0x0D', 16), int('0xFF', 16), 1, 'byte', np.uint8)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(Byte, raw_bytes)


class SignedInt64(np.int64, BaseType):
    metadata = TypeMetadata(14, True, int('0x8E', 16), int('0x7FFFFFFFFFFFFFFF', 16), 8, 'sint64', np.int64)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(SignedInt64, raw_bytes)


class UnsignedInt64(np.uint64, BaseType):
    metadata = TypeMetadata(15, True, int('0x8F', 16), int('0xFFFFFFFFFFFFFFFF', 16), 8, 'uint64', np.uint64)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(UnsignedInt64, raw_bytes)


class UnsignedInt64z(np.uint64, BaseType):
    metadata = TypeMetadata(16, True, int('0x90', 16), int('0x0000000000000000', 16), 8, 'uint64z', np.uint64)

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        return from_bytes(UnsignedInt64z, raw_bytes)


BASE_TYPE_NUMBER_TO_CLASS = {
    FITEnum.metadata.base_type_number: FITEnum,
    SignedInt8.metadata.base_type_number: SignedInt8,
    UnsignedInt8.metadata.base_type_number: UnsignedInt8,
    SignedInt16.metadata.base_type_number: SignedInt16,
    UnsignedInt16.metadata.base_type_number: UnsignedInt16,
    SignedInt32.metadata.base_type_number: SignedInt32,
    UnsignedInt32.metadata.base_type_number: UnsignedInt32,
    String.metadata.base_type_number: String,
    Float32.metadata.base_type_number: Float32,
    Float64.metadata.base_type_number: Float64,
    UnsignedInt8z.metadata.base_type_number: UnsignedInt8z,
    UnsignedInt16z.metadata.base_type_number: UnsignedInt16z,
    UnsignedInt32z.metadata.base_type_number: UnsignedInt32z,
    Byte.metadata.base_type_number: Byte,
    SignedInt64.metadata.base_type_number: SignedInt64,
    UnsignedInt64.metadata.base_type_number: UnsignedInt64,
    UnsignedInt64z.metadata.base_type_number: UnsignedInt64z,
}

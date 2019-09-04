# Copyright 2019 Joan Puig
# See LICENSE for details


import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Union, Tuple, List

import zipfile
import hashlib

import xlrd

from FIT import duplicates

"""
This file provides all the classes and functions related to the loading and parsing of the profile data
The data classes are a 1 to 1 mapping of the content of the excel file
Some data consistency check is done as part of the parsing, further inconsistencies could be found in the code generation step
"""


class ProfileContentError(Exception):
    """This class represents an error due to content in the profile that does not follow the expected format"""
    pass


class ProfileContentWarning(Warning):
    """This class represents a warning due to content in the profile that does not follow the expected format"""
    pass


class SDKContentError(Exception):
    """THis class represents an error due to content in the SDK file that does not follow the expected content"""
    pass


class ProfileVersion(Enum):
    """Enum that keeps track of the known profile versions"""
    Version_21_10_00 = 211000
    Version_20_96_00 = 209600

    @staticmethod
    def current() -> "ProfileVersion":
        return ProfileVersion.Version_20_96_00


"""Mapping of the known SHA signatures of the different SDK version files supported, there must be an entry for each ProfileVersion entry"""
SDK_ZIP_SHA256 = {
    '6CF1BF207B336506C7021BC79F1AC61620380E51A6754CFB4CF74BB8CC527165': ProfileVersion.Version_21_10_00,
    'B0379726606A23105437A3C89B888E831ABEB9B95EDAD8DF1E8C9BAF93F3F8A4': ProfileVersion.Version_20_96_00,
}


@dataclass(frozen=True)
class ValueProfile:
    """Holds the information for a named value in the profile"""
    name: str
    value: Union[str, int]
    comment: str


@dataclass(frozen=True)
class TypeProfile:
    """Holds the information for a type defined in the profile"""
    name: str
    base_type: str
    comment: str
    values: Tuple[ValueProfile]


@dataclass(frozen=True)
class FieldProfile:
    """Holds the information for a field contained within a message in the profile"""
    number: int
    name: str
    type: str
    array: str
    components: str
    scale: int
    offset: int
    units: str
    bits: int
    accumulated: Union[str, int]
    ref_field_name: str
    ref_field_value: str
    comment: str
    product: str
    example: Union[str, int]


DataTable = List[List[Union[None, int, str, float]]]


@dataclass(frozen=True)
class MessageProfile:
    """Holds the information for a message in the profile"""
    name: str
    fields: Tuple[FieldProfile]


@dataclass(frozen=True)
class Profile:
    """Holds the entire profile including types and messages"""
    version: ProfileVersion
    types: Tuple[TypeProfile]
    messages: Tuple[MessageProfile]

    @staticmethod
    def extract_data(sheet: xlrd.sheet.Sheet) -> DataTable:
        """Helper function that extracts cell values from an xlrd sheet into a plain array"""
        cols = sheet.ncols
        rows = sheet.nrows
        return [[sheet.cell_value(row, col) for col in range(0, cols)] for row in range(0, rows)]

    @staticmethod
    def split(table: DataTable) -> List[DataTable]:
        """Splits the content of the profile in its different sections"""
        # Remove empty lines
        table = [row for row in table if not all([cell == '' for cell in row[0:3]])]

        # Every time the first column is not empty, we create a new split
        split_content = []
        for row in table:
            if not row[0] == '':
                split_content.append([])
            split_content[-1].append(row)

        return split_content

    @staticmethod
    def parse_type(type_data: DataTable) -> TypeProfile:
        return TypeProfile(type_data[0][0], type_data[0][1], type_data[0][4], tuple([ValueProfile(*v[2:]) for v in type_data[1:]]))

    @staticmethod
    def to_int(array: List, index: int):
        if array[index] != '':
            array[index] = int(array[index])
        else:
            array[index] = None
        return array

    @staticmethod
    def parse_message(message_data: DataTable) -> MessageProfile:
        return MessageProfile(message_data[0][0], tuple([FieldProfile(*Profile.to_int(f[1:], 0)) for f in message_data[1:]]))

    @staticmethod
    def sha256(file_name: str) -> str:
        """Helper function to compute the SHA256 hash of a given file name"""
        algo = hashlib.sha256()

        with open(file_name, 'rb') as file:
            while True:
                chunk = file.read(algo.block_size)
                if not chunk:
                    break
                algo.update(chunk)

        return algo.hexdigest().upper()

    @staticmethod
    def from_sdk_zip(file_name: str, strict: bool = False) -> "Profile":
        """High level function that given the SDK file will do all the necessary steps to extract a profile"""

        file_hash = Profile.sha256(file_name)
        if file_hash not in SDK_ZIP_SHA256:
            raise SDKContentError(f'The SHA of the input file {file_name} does not match the known SHAs of any supported SDK versions. FYI, the latest supported version is: {ProfileVersion.current().name}')

        version = SDK_ZIP_SHA256[file_hash]

        zf = zipfile.ZipFile(file_name, 'r')
        zip_file_content = zf.read('Profile.xlsx')
        return Profile.from_xlsx(zip_file_content, version, strict)

    @staticmethod
    def from_xlsx(file: str, version: ProfileVersion, strict: bool = False, add_pad_message_profile: bool = True) -> "Profile":
        if type(file) == str:
            book = xlrd.open_workbook(file)
        else:
            book = xlrd.open_workbook(file_contents=file)

        sheet_names = book.sheet_names()

        expected_sheets = ['Types', 'Messages']

        for expected_sheet in expected_sheets:
            if expected_sheet in sheet_names:
                sheet_names.remove(expected_sheet)
            else:
                raise ProfileContentError(f'Profile {version.name} file does not contain a "{expected_sheet}" sheet')

        if sheet_names:
            raise ProfileContentError(f'Profile {version.name} file contains unexpected sheets: {sheet_names}')

        types_sheet = book.sheet_by_name('Types')
        types_table = Profile.extract_data(types_sheet)

        messages_sheet = book.sheet_by_name('Messages')
        messages_table = Profile.extract_data(messages_sheet)

        return Profile.from_tables(types_table, messages_table, version, strict)

    @staticmethod
    def from_tables(types_table: List[List[Union[None, int, str, float]]], messages_table:  List[List[Union[None, int, str, float]]], version: ProfileVersion, strict: bool = False, add_pad_message_profile: bool = True) -> "Profile":
        split_types = Profile.split(types_table[1:])
        types = [Profile.parse_type(type_data) for type_data in split_types]

        duplicate_type_names = duplicates([type_def.name for type_def in types])
        if duplicate_type_names:
            raise ProfileContentError(f'Profile {version.name} has duplicate type names: {", ".join(duplicate_type_names)}')

        split_messages = Profile.split(messages_table[1:])
        messages = [Profile.parse_message(message_data) for message_data in split_messages]

        message_names = [message.name for message in messages]
        duplicate_message_types = duplicates(message_names)
        if duplicate_message_types:
            raise ProfileContentError(f'Profile {version.name} has duplicate message types: {", ".join(duplicate_message_types)}')

        if 'pad' not in message_names and add_pad_message_profile:
            message_names.append('pad')
            messages.append(MessageProfile('pad', ()))

        for type_def in types:
            if type_def.name == 'mesg_num':
                missing_message_type = []

                for value in type_def.values:
                    if (value.name not in message_names) and (value.name not in ['mfg_range_min', 'mfg_range_max']):
                        missing_message_type.append(f'{value.name} ({value.value})')

                if missing_message_type:
                    error_message = f'Profile {version.name} has an entry in mesg_num for [{", ".join(missing_message_type)}] but no corresponding message definition'
                    if strict:
                        raise ProfileContentError(error_message)
                    else:
                        warnings.warn(error_message, ProfileContentWarning)

                missing_mesg_num_value = []
                for message_name in message_names:
                    if message_name not in [value.name for value in type_def.values]:
                        missing_mesg_num_value.append(message_name)

                if missing_mesg_num_value:
                    error_message = f'Profile {version.name} has message definition for [{", ".join(missing_mesg_num_value)}] but no corresponding value in mesg_num'
                    if strict:
                        raise ProfileContentError(error_message)
                    else:
                        warnings.warn(error_message, ProfileContentWarning)

                break

        return Profile(version, tuple(types), tuple(messages))

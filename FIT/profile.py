# Copyright 2019 Joan Puig
# See LICENSE for details

import zipfile
import hashlib
import xlrd
import warnings

from dataclasses import dataclass
from enum import Enum
from typing import Union, Tuple, List, Set, Iterable
from FIT.base_types import BASE_TYPE_NAME_MAP


"""
This file provides all the classes and functions related to the loading and parsing of the profile data
The data classes are a 1 to 1 mapping of the content of the excel file
Some data consistency check is done as part of the parsing, further inconsistencies could be found in the code generation step

The latest FIT SDK file can be obtained from: https://www.thisisant.com/resources/fit/
"""


class ProfileContentError(Exception):
    """
    This class represents an error due to content in the profile that does not follow the expected format
    """
    pass


class ProfileContentWarning(Warning):
    """
    This class represents a warning due to content in the profile that does not follow the expected format
    """
    pass


class SDKContentError(Exception):
    """
    This class represents an error due to content in the SDK file that does not follow the expected content
    """
    pass


class ProfileVersion(Enum):
    """
    Enum that keeps track of the known profile versions
    """
    Version_21_10_00 = 211000
    Version_20_96_00 = 209600

    def version_str(self) -> str:
        """
        Returns a string representation of the version that matches the commonly used format by Garmin
        """
        return self.name[8:].replace("_", ".")

    @staticmethod
    def current() -> "ProfileVersion":
        return ProfileVersion.Version_20_96_00


"""
Mapping of the known SHA signatures of the different SDK version files supported, there must be an entry for each ProfileVersion entry
"""
SDK_ZIP_SHA256 = {
    '6CF1BF207B336506C7021BC79F1AC61620380E51A6754CFB4CF74BB8CC527165': ProfileVersion.Version_21_10_00,
    'B0379726606A23105437A3C89B888E831ABEB9B95EDAD8DF1E8C9BAF93F3F8A4': ProfileVersion.Version_20_96_00,
}


@dataclass(frozen=True)
class ValueProfile:
    """
    Holds the information for a named value in the profile
    """
    name: str
    value: Union[str, int]
    comment: str


@dataclass(frozen=True)
class TypeProfile:
    """
    Holds the information for a type defined in the profile
    """
    name: str
    base_type: str
    comment: str
    values: Tuple[ValueProfile]


@dataclass(frozen=True)
class FieldProfile:
    """
    Holds the information for a field contained within a message in the profile
    """
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


# Type alias for the contents of the xl sheet
DataRow = List[Union[None, int, str, float]]
DataTable = List[DataRow]


@dataclass(frozen=True)
class MessageProfile:
    """
    Holds the information for a message in the profile
    """
    name: str
    fields: Union[Tuple[()], Tuple[FieldProfile]]


@dataclass(frozen=True)
class Profile:
    """
    Holds the entire profile including types and messages
    """
    version: ProfileVersion
    types: Tuple[TypeProfile]
    messages: Tuple[MessageProfile]

    @staticmethod
    def duplicates(elements: Iterable) -> Set:
        """
        Returns a set of elements that appear more than once in the input iterable
        """
        s = set()
        return set(element for element in elements if element in s or s.add(element))

    @staticmethod
    def _non_fatal_error(message: str, strict: bool = False):
        """
        Issues a error or warning given a non fatal error message depending on the strict input
        """
        if strict:
            raise ProfileContentError(message)
        else:
            warnings.warn(message, ProfileContentWarning)

    @staticmethod
    def _parse_type(type_data: DataTable, version: ProfileVersion, strict: bool = False) -> TypeProfile:
        """
        This low level function will return a TypeProfile given a plain data table. The first row should contain the type name,
         base type and a comment the following rows should contain the data for the type named values
        """

        # Check that the profile has at least one row
        if len(type_data) == 0:
            raise ProfileContentError(f'Profile {version.version_str()} empty type data table')

        # Check that the profile has 5 and only 5 columns
        for row in type_data:
            if len(row) != 5:
                raise ProfileContentError(f'Profile {version.version_str()} expecting row length of 5, got {len(row)}')

        # Replace floating point constant into ints as xlrd will load ints as floats
        for row in type_data:
            if isinstance(row[3], float):
                row[3] = int(row[3])

        type_profile = TypeProfile(type_data[0][0], type_data[0][1], type_data[0][4], tuple([ValueProfile(*v[2:]) for v in type_data[1:]]))

        # Check that the type name is not empty
        if not type_profile.name:
            raise ProfileContentError(f'Profile {version.version_str()} has empty type name')

        # Check that the base type is known
        if type_profile.base_type not in BASE_TYPE_NAME_MAP.keys():
            raise ProfileContentError(f'Profile {version.version_str()} type {type_profile} has unknown base type: {type_profile.base_type}')

        # Check no empty value names
        for value in type_profile.values:
            if not value.name:
                raise ProfileContentError(f'Profile {version.version_str()} in type {type_profile.name} has empty value name')

        # Check no empty values
        for value in type_profile.values:
            if value.value is None or value.value == '':
                raise ProfileContentError(f'Profile {version.version_str()} in type {type_profile.name} has empty value for name {value.name}')

        # Check no duplicate value names
        duplicates = Profile.duplicates([value.name for value in type_profile.values])
        if duplicates:
            Profile._non_fatal_error(f'Profile {version.version_str()} in type {type_profile.name} has duplicate values names: {", ".join(duplicates)}', strict)

        # Check no duplicate values
        duplicates = Profile.duplicates([value.value for value in type_profile.values])
        if duplicates:
            Profile._non_fatal_error(f'Profile {version.version_str()} in type {type_profile.name} has duplicate values: {", ".join([str(duplicate) for duplicate in duplicates])}', strict)

        return type_profile

    @staticmethod
    def _parse_types(types_table: DataTable, version: ProfileVersion, strict: bool = True) -> Tuple[TypeProfile]:
        """
        Low level function that given the types data will return a tuple of types. It will also perform some consistency checks
        """
        # Check at least one row (the header row)
        if len(types_table) == 0:
            raise ProfileContentError(f'Profile {version.version_str()} has empty types data')

        # Split the contents of the types ignoring the first row which are the headers
        split_types = Profile._split(types_table[1:])
        types = [Profile._parse_type(type_data, version, strict) for type_data in split_types]

        # Check for duplicate types
        duplicate_type_names = Profile.duplicates(type_def.name for type_def in types)
        if duplicate_type_names:
            raise ProfileContentError(f'Profile {version.version_str()} has duplicate type names: {", ".join(duplicate_type_names)}')

        return tuple(types)

    @staticmethod
    def _to_int(array: DataRow, index: int):
        """
        Helper function that will cast a given index of a list into int unless the value is '' in which case it will replace it with None
        """
        if array[index] != '':
            array[index] = int(array[index])
        else:
            array[index] = None
        return array

    @staticmethod
    def _parse_message(message_data: DataTable) -> MessageProfile:
        """
        This function will return a MessageProfile given a plain data table. The first row should contain the message name
        the following rows should contain the data for the message fields
        """
        return MessageProfile(message_data[0][0], tuple([FieldProfile(*Profile._to_int(f[1:], 0)) for f in message_data[1:]]))

    @staticmethod
    def _extract_data(sheet: xlrd.sheet.Sheet) -> DataTable:
        """
        Helper function that extracts cell values from an xlrd sheet into a plain array
        """

        cols = sheet.ncols
        rows = sheet.nrows
        return [[sheet.cell_value(row, col) for col in range(0, cols)] for row in range(0, rows)]

    @staticmethod
    def _parse_messages(messages_table: DataTable, version: ProfileVersion, strict: bool = False, add_pad_message_profile: bool = True) -> Tuple[MessageProfile]:
        # Split the contents of the messages ignoring the first row which are the headers
        split_messages = Profile._split(messages_table[1:])
        messages = [Profile._parse_message(message_data) for message_data in split_messages]

        # Check for duplicate messages
        message_names = [message.name for message in messages]
        duplicate_message_types = Profile.duplicates(message_names)
        if duplicate_message_types:
            raise ProfileContentError(f'Profile {version.version_str()} has duplicate message types: {", ".join(duplicate_message_types)}')

        # We add a pad message if required
        if 'pad' not in message_names and add_pad_message_profile:
            message_names.append('pad')
            messages.append(MessageProfile('pad', ()))

        return tuple(messages)

    @staticmethod
    def _split(table: DataTable) -> List[DataTable]:
        """
        Helper function to splits the content of a profile sheet in its different sections
        """

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
    def _from_tables(types_table: DataTable, messages_table: DataTable, version: ProfileVersion, strict: bool = False, add_pad_message_profile: bool = True) -> "Profile":
        """
        Low level function that given plain data corresponding to the profile information will create a profile object
        There are certain inconsistencies in the file that by default are just reported as a warning use strict=True to turn them into errors
        Pad is a special type of message that contains no fields. It has an entry in mseg_num, but no corresponding message definition
        by default a message profile entry will be created for pad, use add_pad_message_profile=False to disable that
        To get more information on pad see: https://www.thisisant.com/forum/viewthread/7217/
        """

        types = Profile._parse_types(types_table, version)
        messages = Profile._parse_messages(messages_table, version, strict, add_pad_message_profile)

        # We find the mesg_num type definition since we know it is an enum like type that contains all the known messages
        mesg_num_def = None
        for type_def in types:
            if type_def.name == 'mesg_num':
                mesg_num_def = type_def
                break

        # If there is no mesg_num type, the profile data is inconsistent
        if not mesg_num_def:
            raise ProfileContentError('The profile does not contain a "mesg_num" type definition')

        # We perform some consistency checks
        message_names = [message.name for message in messages]
        missing_message_type = []
        for value in mesg_num_def.values:
            if value.name not in message_names:  # If there is no message found
                if value.name not in ['mfg_range_min', 'mfg_range_max']:  # And the name is not one of the manufacturer specific range constants
                    missing_message_type.append(f'{value.name} ({value.value})')  # We add it to the missing messages

        # Issue the errors / warnings
        if missing_message_type:
            error_message = f'Profile {version.version_str()} has an entry in mesg_num for [{", ".join(missing_message_type)}] but no corresponding message definition'
            if strict:
                raise ProfileContentError(error_message)
            else:
                warnings.warn(error_message, ProfileContentWarning)

        # We check for messages that have been defined, but do not have a corresponding entry in mesg_num
        missing_mesg_num_value = []
        for message_name in message_names:
            if message_name not in [value.name for value in mesg_num_def.values]:
                missing_mesg_num_value.append(message_name)

        # Issue the errors / warnings
        if missing_mesg_num_value:
            error_message = f'Profile {version.version_str()} has message definition for [{", ".join(missing_mesg_num_value)}] but no corresponding value in mesg_num'
            if strict:
                raise ProfileContentError(error_message)
            else:
                warnings.warn(error_message, ProfileContentWarning)

        return Profile(version, types, messages)

    @staticmethod
    def from_xlsx(file: Union[str, bytes], version: ProfileVersion, strict: bool = False, add_pad_message_profile: bool = True) -> "Profile":
        """
        This high level function will take either the file name or the bytes content of the file and parse the corresponding profile
        See from_tables() for information on the optional arguments
        """

        # Get the contents of the xlsx file
        if type(file) == str:
            book = xlrd.open_workbook(file)
        else:
            book = xlrd.open_workbook(file_contents=file)

        xl_sheet_names = book.sheet_names()

        # Check that the sheet names are as expected
        expected_sheets = ['Types', 'Messages']
        for expected_sheet in expected_sheets:
            if expected_sheet in xl_sheet_names:
                xl_sheet_names.remove(expected_sheet)
            else:
                raise ProfileContentError(f'Profile {version.name} file does not contain a "{expected_sheet}" sheet')
        if xl_sheet_names:
            raise ProfileContentError(f'Profile {version.name} file contains unexpected sheets: {xl_sheet_names}')

        # Get the plain data content for the types
        types_sheet = book.sheet_by_name('Types')
        types_table = Profile._extract_data(types_sheet)

        # Get the plain data content for the messages
        messages_sheet = book.sheet_by_name('Messages')
        messages_table = Profile._extract_data(messages_sheet)

        # Hand over to the profile parser from plain data
        return Profile._from_tables(types_table, messages_table, version, strict, add_pad_message_profile)

    @staticmethod
    def _sha256(file_name: str) -> str:
        """
        Helper function to compute the SHA256 hash of a given file name
        """

        algo = hashlib.sha256()

        with open(file_name, 'rb') as file:
            while True:
                chunk = file.read(algo.block_size)
                if not chunk:
                    break
                algo.update(chunk)

        return algo.hexdigest().upper()

    @staticmethod
    def from_sdk_zip(file_name: str, strict: bool = False, add_pad_message_profile: bool = True) -> "Profile":
        """
        High level function that given the SDK file will do all the necessary steps to extract a profile
        It is the most convenient way to create a profile object
        See from_tables() for information on the optional arguments
        """

        # Compute the hash and check that it is a known version
        file_hash = Profile._sha256(file_name)
        if file_hash not in SDK_ZIP_SHA256:
            raise SDKContentError(f'The SHA of the input file {file_name} does not match the known SHAs of any supported SDK versions. FYI, the latest supported version is: {ProfileVersion.current().name}')

        # Get the corresponding version
        version = SDK_ZIP_SHA256[file_hash]

        # Extract the Profile.xlsx from the zip file
        zf = zipfile.ZipFile(file_name, 'r')
        zip_file_content = zf.read('Profile.xlsx')

        # Hand over to the profile parser given an xlsx file
        return Profile.from_xlsx(zip_file_content, version, strict, add_pad_message_profile)

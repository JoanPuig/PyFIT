# Copyright 2019 Joan Puig
# See LICENSE for details


from dataclasses import dataclass
from enum import Enum
from typing import List, Union

import zipfile
import hashlib

import xlrd


class UnexpectedProfileContent(Exception):
    pass


class UnexpectedSDKContent(Exception):
    pass


class ProfileVersion(Enum):
    Version_21_10_00 = 211000
    Version_20_96_00 = 209600

    @staticmethod
    def current():  # TODO type safety
        return ProfileVersion.Version_20_96_00


SDK_ZIP_SHA256 = {
    '6CF1BF207B336506C7021BC79F1AC61620380E51A6754CFB4CF74BB8CC527165': ProfileVersion.Version_21_10_00,
    'B0379726606A23105437A3C89B888E831ABEB9B95EDAD8DF1E8C9BAF93F3F8A4': ProfileVersion.Version_20_96_00,
}


@dataclass
class Value:
    name: str
    value: Union[str, int]
    comment: str


@dataclass
class TypeProfile:
    name: str
    base_type: str
    comment: str
    values: List[Value]


@dataclass
class FieldProfile:
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


@dataclass
class MessageProfile:
    name: str
    fields: List[FieldProfile]


@dataclass
class Profile:
    version: ProfileVersion
    types: List[TypeProfile]
    messages: List[MessageProfile]

    @staticmethod
    def extract_data(sheet):
        cols = sheet.ncols
        rows = sheet.nrows
        return [[sheet.cell_value(row, col) for col in range(0, cols)] for row in range(0, rows)]

    @staticmethod
    def split(raw_content):
        # Remove empty lines
        raw_content = [row for row in raw_content if not all([cell == '' for cell in row[0:3]])]

        # Every time the first column is not empty, we create a new split
        split_content = []
        for row in raw_content:
            if not row[0] == '':
                split_content.append([])
            split_content[-1].append(row)

        return split_content

    @staticmethod
    def parse_type(type_data):
        return TypeProfile(type_data[0][0], type_data[0][1], type_data[0][4], [Value(*v[2:]) for v in type_data[1:]])

    @staticmethod
    def parse_message(message_data):
        return MessageProfile(message_data[0][0], [FieldProfile(*f[1:]) for f in message_data[1:]])

    @staticmethod
    def sha256(file_name: str):
        algo = hashlib.sha256()

        with open(file_name, 'rb') as file:
            while True:
                chunk = file.read(algo.block_size)
                if not chunk:
                    break
                algo.update(chunk)

        return algo.hexdigest().upper()

    @staticmethod
    def parse_sdk_zip(file_name: str):  # TODO type check  -> Profile:
        file_hash = Profile.sha256(file_name)

        if file_hash not in SDK_ZIP_SHA256:
            raise UnexpectedSDKContent('The SHA of the input file {} does not match the known SHAs of any supported SDK versions. FYI, the latest supported version is: {}'.format(file_name, ProfileVersion.current().name))

        version = SDK_ZIP_SHA256[file_hash]

        zf = zipfile.ZipFile(file_name, 'r')
        zip_file_content = zf.read('Profile.xlsx')
        return Profile.parse_xlsx(zip_file_content, version)

    @staticmethod
    def parse_xlsx(file: str, version: ProfileVersion):  # TODO type check -> Profile:
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
                raise UnexpectedProfileContent('Profile file does not contain a "{}" sheet'.format(expected_sheet))

        if sheet_names:
            raise UnexpectedProfileContent('Profile file contains unexpected sheets: {}'.format(sheet_names))

        types_sheet = book.sheet_by_name('Types')
        raw_types = Profile.extract_data(types_sheet)
        split_types = Profile.split(raw_types[1:])
        types = [Profile.parse_type(type_data) for type_data in split_types]

        messages_sheet = book.sheet_by_name('Messages')
        raw_messages = Profile.extract_data(messages_sheet)
        split_messages = Profile.split(raw_messages[1:])
        messages = [Profile.parse_message(message_data) for message_data in split_messages]

        return Profile(version, types, messages)

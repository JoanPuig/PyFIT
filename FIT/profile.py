# Copyright 2019 Joan Puig
# See LICENSE for details


from dataclasses import dataclass
from typing import List, Union

import xlrd


class UnexpectedProfileContent(Exception):
    pass


@dataclass
class Value:
    name: str
    value: Union[str, int]
    comment: str


@dataclass
class Type:
    name: str
    base_type: str
    values: List[Value]


@dataclass
class Field:
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
class Message:
    name: str
    fields: List[Field]


@dataclass
class Profile:
    types: List[Type]
    messages: List[Message]


def extract_data(sheet):
    cols = sheet.ncols
    rows = sheet.nrows
    return [[sheet.cell_value(row, col) for col in range(0, cols)] for row in range(0, rows)]


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


def parse_type(type_data):
    return Type(type_data[0][0], type_data[0][1], [Value(*v[2:]) for v in type_data[1:]])


def parse_message(message_data):
    return Message(message_data[0][0], [Field(*f[1:]) for f in message_data[1:]])


def parse(file_name: str):
    book = xlrd.open_workbook(file_name)

    sheet_names = book.sheet_names()

    expected_sheets = ['Types', 'Messages']

    for expected_sheet in expected_sheets:
        if expected_sheet in sheet_names:
            sheet_names.remove(expected_sheet)
        else:
            raise UnexpectedProfileContent('Profile file does not contain a "{}" sheet'.format(expected_sheet))

    if len(sheet_names) != 0:
        raise UnexpectedProfileContent('Profile file contains unexpected sheets: {}'.format(sheet_names))

    types_sheet = book.sheet_by_name('Types')
    raw_types = extract_data(types_sheet)
    split_types = split(raw_types[1:])
    types = [parse_type(type_data) for type_data in split_types]

    messages_sheet = book.sheet_by_name('Messages')
    raw_messages = extract_data(messages_sheet)
    split_messages = split(raw_messages[1:])
    messages = [parse_message(message_data) for message_data in split_messages]

    return Profile(types, messages)

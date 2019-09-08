# Copyright 2019 Joan Puig
# See LICENSE for details


import importlib
import keyword
import datetime

from pathlib import Path
from typing import Iterable, Optional

from FIT.profile import Profile, MessageScalarFieldProfile
from FIT.base_types import BASE_TYPE_NAME_MAP


class CodeWriterError(Exception):
    """
    Code writer error
    """
    pass


class CodeWriter:
    """
    Helper class that appends code fragments and manages indentation for code generation
    """
    def __init__(self):
        self.indent_count = 0
        self.content = ''
        self.in_fragment = False

    def indent(self):
        """
        Indents all the code written after
        """
        if self.in_fragment:
            raise CodeWriterError('Cannot indent while writing a line fragment')
        self.indent_count = self.indent_count + 1

    def unindent(self):
        """
        Unindents all the code written after
        """
        if self.in_fragment:
            raise CodeWriterError('Cannot unindent while writing a line fragment')
        self.indent_count = self.indent_count - 1

    def write(self, code: str):
        """
        Writes a line of code
        """
        self.write_fragment(code)
        self.new_line()

    def new_line(self, lines: int = 1):
        """
        Writes a new line, and terminates the fragment if it was inside one
        """
        self.content = self.content + ('\n'*lines).format()
        self.in_fragment = False

    def write_fragment(self, code: str):
        """
        Writes a partial line of code, new lines will continue at the end of this fragment without a new line being added
        """
        if self.in_fragment:
            self.content = self.content + code
        else:
            self.content = self.content + ('\t'*self.indent_count).format() + code

        self.in_fragment = True

    def write_to_file(self, file_name: str):
        """
        Writes the current code to a file
        """
        if self.in_fragment:
            self.new_line()

        with open(file_name, 'w') as file:
            file.write(self.content)


class CodeGeneratorError(Exception):
    """
    Code generation error
    """
    pass


class CodeGenerator:
    """
    Base class of the code generators that provides common functionality
    """
    def __init__(self, profile: Profile, code_writer: CodeWriter):
        self.profile = profile

        if code_writer:
            self.code_writer = code_writer
        else:
            self.code_writer = CodeWriter()

    def _generate_header(self):
        """
        Writes standard header
        """
        cw = self.code_writer
        cw.write('# Copyright 2019 Joan Puig')
        cw.write('# See LICENSE for details')
        cw.new_line()
        cw.write(f'# Generated by {self.__class__.__name__} in {Path(__file__).name} based on profile version {self.profile.version.version_str()} on {datetime.datetime.now():%Y-%m-%d %H:%M:%S}')

    def _generate_base_type_imports(self):
        cw = self.code_writer
        cw.write('from FIT.base_types import SignedInt8, SignedInt16, SignedInt32, SignedInt64')
        cw.write('from FIT.base_types import UnsignedInt8, UnsignedInt16, UnsignedInt32, UnsignedInt64')
        cw.write('from FIT.base_types import UnsignedInt8z, UnsignedInt16z, UnsignedInt32z, UnsignedInt64z')
        cw.write('from FIT.base_types import FITEnum, String, Float32, Float64, Byte')

    def _generate_version(self):
        """
        Adds a constant representing the profile version that was used to generate the code
        """
        self.code_writer.write(f'PROFILE_VERSION = ProfileVersion.{self.profile.version.name}')

    @staticmethod
    def _capitalize_type_name(name: str) -> str:
        """
        Capitalizes a string input
        """
        return ''.join(c[0].capitalize() + c[1:] for c in name.split('_'))

    @staticmethod
    def _check_valid_name(name: str) -> None:
        """
        Errors if the name identifier is invalid, meaning, it is empty, a keyword or starts with a digit
        """
        if not name:
            raise CodeGeneratorError('Name is empty')
        if keyword.iskeyword(name):
            raise CodeGeneratorError(f'Name {name} is a keyword')
        if name[0].isdigit():
            raise CodeGeneratorError(f'Name {name} starts with a digit')

    @staticmethod
    def _generate(code_generator, output_file: Optional[str] = None) -> str:
        """
        Called by the child classes to generate code and output to file
        """
        code_generator._generate_full()

        if output_file:
            code_generator.code_writer.write_to_file(output_file)

        return code_generator.code_writer.content


class TypeCodeGenerator(CodeGenerator):

    def __init__(self, profile: Profile, code_writer: CodeWriter = None):
        """
        Some types appear to be enums in the profile, but in reality can take any value.
        """
        super().__init__(profile, code_writer)

    def _generate_full(self):
        self._generate_header()
        self.code_writer.new_line(2)
        self._generate_imports()
        self.code_writer.new_line(2)
        self._generate_version()
        self.code_writer.new_line(2)
        self._generate_types()

    def _generate_imports(self):
        cw = self.code_writer
        cw.write('from enum import Enum, auto')
        cw.new_line()
        self._generate_base_type_imports()
        cw.new_line()
        cw.write('from FIT.profile import ProfileVersion')

    def _generate_types(self):
        cw = self.code_writer
        types = self.profile.types

        for type_profile in types:
            type_name = CodeGenerator._capitalize_type_name(type_profile.name)
            CodeGenerator._check_valid_name(type_name)

            cw.write(f'# FIT type name: {type_profile.name}')
            if type_profile.comment:
                cw.write(f'# {type_profile.comment}')

            if type_profile.is_enum:
                cw.write(f'class {type_name}(Enum):')
            else:
                cw.write(f'class {type_name}({BASE_TYPE_NAME_MAP[type_profile.base_type]}):')

            cw.indent()

            has_invalid = False
            has_invalid_value = False
            mod = importlib.import_module('FIT.base_types')
            type_class = getattr(mod, BASE_TYPE_NAME_MAP[type_profile.base_type])
            parent_type_invalid_value = type_class.metadata().invalid_value
            resolved_values = []
            for value in type_profile.values:
                value_name = CodeGenerator._capitalize_type_name(value.name)
                CodeGenerator._check_valid_name(value_name)

                if isinstance(value.value, str):
                    value_str = f'{value.value}'
                    if int(value.value, 0) == parent_type_invalid_value:
                        has_invalid_value = True
                else:
                    value_str = f'{int(value.value):d}'
                    if int(value.value) == parent_type_invalid_value:
                        has_invalid_value = True

                resolved_values.append({
                    'value_name': value_name,
                    'base_type': BASE_TYPE_NAME_MAP[type_profile.base_type],
                    'value_str': value_str,
                    'original_value_name': value.name,
                    'comment': value.comment}
                )

                if value_name == 'Invalid':
                    has_invalid = True

            if not has_invalid and not has_invalid_value:
                resolved_values.append({
                    'value_name': 'Invalid',
                    'base_type': BASE_TYPE_NAME_MAP[type_profile.base_type],
                    'value_str': f'{parent_type_invalid_value}',
                    'original_value_name': 'Invalid',
                    'comment': 'Invalid value'}
                )

            max_name_length = max([len(resolved_value['value_name']) for resolved_value in resolved_values])
            max_value_length = max([len(resolved_value['value_str']) for resolved_value in resolved_values])
            max_original_name_length = max([len(resolved_value['original_value_name']) for resolved_value in resolved_values])
            fmt = '{:<' + str(max_name_length) + '} = {}({:>' + str(max_value_length) + '})  # {:<' + str(max_original_name_length) + '}'

            for resolved_value in resolved_values:
                cw.write_fragment(fmt.format(resolved_value['value_name'], resolved_value['base_type'], resolved_value['value_str'], resolved_value['original_value_name']))
                if resolved_value['comment']:
                    cw.write(f' - {resolved_value["comment"]}')
                else:
                    cw.write('')

            cw.unindent()
            cw.new_line(2)

    @staticmethod
    def generate(profile: Profile, output_file:  Optional[str] = None, **kwargs) -> str:
        code_generator = TypeCodeGenerator(profile, **kwargs)
        return CodeGenerator._generate(code_generator, output_file)


class MessageCodeGenerator(CodeGenerator):

    def __init__(self, profile: Profile, code_writer: CodeWriter = None):
        super().__init__(profile, code_writer)

    def _generate_full(self):
        self._generate_header()
        self.code_writer.new_line(2)
        self._generate_imports()
        self.code_writer.new_line(2)
        self._generate_version()
        self.code_writer.new_line(2)
        self._generate_units()
        self.code_writer.new_line(2)
        self._generate_messages()

    def _generate_imports(self):
        cw = self.code_writer
        cw.write('import warnings')
        cw.write('import functools')
        cw.write('from typing import Tuple, Dict, Union')
        cw.write('from enum import Enum, auto')
        cw.write('from dataclasses import dataclass')
        cw.new_line()
        self._generate_base_type_imports()
        cw.new_line()
        cw.write('import FIT.types')
        cw.write('from FIT.model import Record, Message, MessageDefinition, FieldDefinition, RecordField, FieldMetadata, MessageMetadata, DeveloperMessageField, UndocumentedMessageField')
        cw.write('from FIT.profile import ProfileVersion')

    def _generate_units(self):
        cw = self.code_writer
        messages = self.profile.messages

        cw.write('class Unit(Enum):')
        cw.indent()
        for unit in self.profile.units():
            CodeGenerator._check_valid_name(unit)
            cw.write(f'{unit} = auto()')
        cw.unindent()

    def _generate_messages(self):
        cw = self.code_writer
        messages = self.profile.messages

        for message in messages:
            message_name = CodeGenerator._capitalize_type_name(message.name)
            cw.write('@dataclass(frozen=True)')
            cw.write(f'# FIT message name: {message.name}')
            cw.write(f'class {message_name}(Message):')
            cw.indent()

            resolved_fields = []
            for field in message.fields:
                CodeGenerator._check_valid_name(field.name)

                if field.type in BASE_TYPE_NAME_MAP:
                    rf = {'name': field.name, 'type': CodeGenerator._capitalize_type_name(BASE_TYPE_NAME_MAP[field.type]), 'comment': field.comment}
                else:
                    # Need to keep the FIT.types prefix as there are some messages that have the same name as some types
                    rf = {'name': field.name, 'type': 'FIT.types.' + CodeGenerator._capitalize_type_name(field.type), 'comment': field.comment}
                resolved_fields.append(rf)

            if resolved_fields:
                max_name_length = max([len(resolved_field['name']) for resolved_field in resolved_fields])
                max_type_length = max([len(resolved_field['type']) for resolved_field in resolved_fields])

                for rf in resolved_fields:
                    CodeGenerator._check_valid_name(rf['name'])
                    fmt = '{:<' + str(max_name_length) + '} : {:<' + str(max_type_length) + '}'
                    cw.write_fragment(fmt.format(rf['name'], rf['type']))
                    if rf['comment']:
                        cw.write(f'    # {rf["comment"]}')
                    else:
                        cw.write('')

            cw.new_line()
            cw.write('@staticmethod')
            cw.write('def expected_field_numbers() -> Tuple[int]:')
            cw.indent()
            if len(message.fields) == 0:
                cw.write('return ()')
            elif len(message.fields) == 1:
                cw.write(f'return ({message.fields[0].number},)')
            else:
                cw.write(f'return ({", ".join([str(field.number) for field in message.fields if field.number is not None])})')
            cw.unindent()
            cw.new_line()
            cw.write('@staticmethod')
            cw.write(f'def from_extracted_fields(extracted_fields, developer_fields: Tuple[DeveloperMessageField], undocumented_fields: Tuple[UndocumentedMessageField], error_on_invalid_enum_value: bool) ->  "{message_name}":')
            cw.indent()
            if len(message.fields) > 0:
                cw.new_line()
                for field in message.fields:
                    # TODO: the actual fun part
                    if field.number is not None:
                        cw.write(f'{field.name} = extracted_fields[{field.number}]')
                    else:
                        cw.write(f'{field.name} = None')

            common_fields = ['developer_fields', 'undocumented_fields']
            cw.new_line()
            cw.write(f'return {message_name}({", ".join(common_fields + [m.name for m in message.fields])})')
            cw.new_line(2)
            cw.unindent()
            cw.unindent()

    @staticmethod
    def generate(profile: Profile, output_file: Optional[str] = None, **kwargs) -> str:
        code_generator = MessageCodeGenerator(profile, **kwargs)
        return CodeGenerator._generate(code_generator, output_file)

# Copyright 2019 Joan Puig
# See LICENSE for details


import functools
import zipfile
import hashlib
import xlrd
import warnings

from dataclasses import dataclass
from enum import Enum
from typing import Union, Tuple, List, Set, Iterable, Optional
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
class NamedValueProfile:
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
    is_enum: bool
    comment: str
    values: Tuple[NamedValueProfile]


@dataclass(frozen=True)
class ComponentProfile:
    destination_field: Optional[str]
    scale: Optional[int]
    offset: Optional[int]
    units: Optional[str]
    bits: Optional[int]
    accumulated: Optional[bool]


@dataclass(frozen=True)
class DynamicFieldMatcher:
    ref_field_name: str
    ref_field_value: str


@dataclass(frozen=True)
class MessageFieldProfile:
    """
    Holds the information for a field contained within a message in the profile
    """
    number: int
    name: str
    type: str
    array: Optional[str]
    comment: str
    product: str
    example: Union[str, int]
    dynamic_field_matchers: Union[Tuple[()], Tuple[DynamicFieldMatcher]]


@dataclass(frozen=True)
class MessageScalarFieldProfile(MessageFieldProfile):
    """
    Holds the information for a scalar field contained within a message in the profile
    """
    scale: Optional[int]
    offset: Optional[int]
    units: Optional[str]
    accumulated: Optional[bool]


@dataclass(frozen=True)
class MessageComponentFieldProfile(MessageFieldProfile):
    """
    Holds the information for a component field contained within a message in the profile
    """
    components: Tuple[ComponentProfile]


# Type alias for the contents of the xl sheet
DataRow = List[Union[None, int, str, float]]
DataTable = List[DataRow]


@dataclass(frozen=True)
class MessageProfile:
    """
    Holds the information for a message in the profile
    """
    name: str
    fields: Union[Tuple[()], Tuple[MessageFieldProfile]]


class ProfileCorrector:
    """
    The "raw" profile sometimes contains inconsistencies, missing values, extra values, etc
    The profile corrector will be used to correct them.
    """

    INVALID_VALUE_NAMES = {
        'none': 'Null',
        '4iiiis': 'Innovations4iiiis',
        '1partcarbon': 'OnePartCarbon',
        '3_way_calf_raise': 'ThreeWayCalfRaise',
        '3_way_weighted_calf_raise': 'ThreeWayWeightedCalfRaise',
        '3_way_single_leg_calf_raise': 'ThreeWaySingleLegCalfRaise',
        '3_way_weighted_single_leg_calf_raise': 'ThreeWayWeightedSingleLegCalfRaise',
        '45_degree_cable_external_rotation': 'FortyFiveDegreeCableExternalRotation',
        '45_degree_plank': 'FortyFiveDegreePlank',
        '90_degree_static_hold': 'NinetyDegreeStaticHold',
        '30_degree_lat_pulldown': 'ThirtyDegreeLatPulldown',
        '90_degree_cable_external_rotation': 'NinetyDegreeCableExternalRotation',
    }

    INVALID_UNITS = {
        '2 * cycles (steps)': 'two_cycles_steps',
        '100 * m': 'length_100_m',
        'min': 'minutes',
        'deg/s': 'degrees/s',
        'C': 'degrees_celsius',
        'if': 'intensity_factor',
        'tss': 'training_stress_score',
        'mmHg': 'mm_Hg',
        '': 'dimensionless',
    }

    FREE_RANGE_TYPES = (
        'message_index',
        'user_local_id',
        'fit_base_unit',
        'date_time',
        'local_date_time',
        'device_index'
    )

    @staticmethod
    def correct_named_value(named_value_profile: NamedValueProfile) -> NamedValueProfile:
        old_name = named_value_profile.name
        new_name = ProfileCorrector.INVALID_VALUE_NAMES.get(old_name, old_name)
        return NamedValueProfile(new_name, named_value_profile.value, named_value_profile.comment)

    @staticmethod
    def correct_named_values(named_value_profiles: Union[Tuple[()], Tuple[NamedValueProfile]]) -> Union[Tuple[()], Tuple[NamedValueProfile]]:
        return named_value_profiles

    @staticmethod
    def correct_type(type_profile: TypeProfile) -> TypeProfile:
        if type_profile.name == 'weather_report':
            # According to the comment: forecast is deprecated use hourly_forecast instead
            named_values = tuple([named_value for named_value in type_profile.values if named_value.name != 'forecast'])
            return TypeProfile(type_profile.name, type_profile.base_type, type_profile.is_enum, type_profile.comment, named_values)

        # Some types appear to be enums since they have named values in them, but they can in fact take any value
        if type_profile.name in ProfileCorrector.FREE_RANGE_TYPES:
            return TypeProfile(type_profile.name, type_profile.base_type, False, type_profile.comment, type_profile.values)

        return type_profile

    @staticmethod
    def correct_types(type_profiles: Union[Tuple[()], Tuple[TypeProfile]]) -> Union[Tuple[()], Tuple[TypeProfile]]:
        # A bool type is referenced but not defined either as a base type or derived
        # https://www.thisisant.com/forum/viewthread/6656/

        # Must be all capitals otherwise it conflicts with Pythons True / False
        named_values = (
            NamedValueProfile('TRUE', 1, ''),
            NamedValueProfile('FALSE', 0, '')
        )

        bool_type = TypeProfile('bool', 'uint8', True, 'Manually added, see: https://www.thisisant.com/forum/viewthread/6656/', named_values)
        return (bool_type,) + type_profiles

    @staticmethod
    def correct_message_field(fp: MessageFieldProfile) -> MessageFieldProfile:
        # The profile file provided in the SDK has inconsistent names for units, the following code cleans them up

        # Replace some illegal characters in the unit names
        def clean_unit(u: Optional[str]) -> Optional[str]:
            if u is None:
                return None
            else:
                return ProfileCorrector.INVALID_UNITS.get(u, u).replace(' ', '_').replace('^', '').replace('/', '_per_').replace('%', 'percent')

        if isinstance(fp, MessageComponentFieldProfile):
            new_components = []
            for c in fp.components:
                new_components.append(ComponentProfile(c.destination_field, c.scale, c.offset, clean_unit(c.units), c.bits, c.accumulated))
            return MessageComponentFieldProfile(fp.number, fp.name, fp.type, fp.array, fp.comment, fp.product, fp.example, fp.dynamic_field_matchers, tuple(new_components))
        elif isinstance(fp, MessageScalarFieldProfile):
            return MessageScalarFieldProfile(fp.number, fp.name, fp.type, fp.array, fp.comment, fp.product, fp.example, fp.dynamic_field_matchers, fp.scale, fp.offset, clean_unit(fp.units), fp.accumulated)
        else:
            raise ProfileContentError(f'Unexpected MessageFieldProfile implementation {type(fp)}')

    @staticmethod
    def correct_message_fields(field_profiles: Union[Tuple[()], Tuple[MessageFieldProfile]]) -> Union[Tuple[()], Tuple[MessageFieldProfile]]:
        return field_profiles

    @staticmethod
    def correct_message(message: MessageProfile) -> MessageProfile:
        return message

    @staticmethod
    def correct_messages(messages: Union[Tuple[()], Tuple[MessageProfile]]) -> Union[Tuple[()], Tuple[MessageProfile]]:
        # Pad is a special type of message that contains no fields. It has an entry in mseg_num, but no corresponding message definition
        # To get more information on pad see: https://www.thisisant.com/forum/viewthread/7217/
        return messages + tuple([MessageProfile('pad', ())])

    @staticmethod
    def correct_profile(profile: "Profile") -> "Profile":
        return profile


class ProfileCorrector211000(ProfileCorrector):
    """
    Extends the base ProfileCorrector to account for the 21.10.00 version specific corrections
    """
    pass


class ProfileCorrector209600(ProfileCorrector):
    """
    Extends the base ProfileCorrector to account for the 20.96.00 version specific corrections
    """
    pass


"""
Given a profile version, you will be able to obtain the class of the default corrector for that version
"""
DEFAULT_PROFILE_CORRECTOR = {
    ProfileVersion.Version_21_10_00: ProfileCorrector211000(),
    ProfileVersion.Version_20_96_00: ProfileCorrector209600(),
}


@dataclass(frozen=True)
class Profile:
    """
    Holds the entire profile including types and messages
    """
    version: ProfileVersion
    types: Tuple[TypeProfile]
    messages: Tuple[MessageProfile]

    @functools.lru_cache(1)
    def units(self) -> Tuple[str]:
        """
        Extracts the list of all the units
        """

        units = set()
        for message in self.messages:
            for field in message.fields:
                if isinstance(field, MessageScalarFieldProfile):
                    if field.units:
                        units.add(field.units)
                elif isinstance(field, MessageComponentFieldProfile):
                    for component in field.components:
                        if component.units:
                            units.add(component.units)
                else:
                    raise ProfileContentError(f'Unexpected MessageFieldProfile implementation {type(field)}')

        units = list(units)
        units.sort(key=str.lower)

        return tuple(units)

    @staticmethod
    def duplicates(elements: Iterable) -> Set:
        """
        Returns a set of elements that appear more than once in the input iterable
        """
        s = set()
        return set(element for element in elements if element in s or s.add(element))

    @staticmethod
    def _non_fatal_error(message: str, strict: bool):
        """
        Issues a error or warning given a non fatal error message depending on the strict input
        """
        if strict:
            raise ProfileContentError(message)
        else:
            warnings.warn(message, ProfileContentWarning)

    @staticmethod
    def _parse_named_value(row: DataRow, version: ProfileVersion, profile_corrector: ProfileCorrector, type_name: str):
        """
        This low level internal function will parse a named value profile given a data row
        """

        # Replace floating point constant into ints as xlrd will load ints as floats
        Profile._to_int(row, 3)

        # Create and correct the named value profile
        value = NamedValueProfile(*row[2:])
        value = profile_corrector.correct_named_value(value)

        # Check no empty value name
        if not value.name:
            raise ProfileContentError(f'Profile {version.version_str()} in type "{type_name}" has empty value name')

        # Check no empty values
        if value.value is None or value.value == '':
            raise ProfileContentError(f'Profile {version.version_str()} in type "{type_name}" has empty value for name "{value.name}"')

        return value

    @staticmethod
    def _parse_type(type_data: DataTable, version: ProfileVersion, profile_corrector: ProfileCorrector, strict: bool) -> TypeProfile:
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

        # Check that the type name is not empty
        type_name = type_data[0][0]
        if not isinstance(type_name, str) or type_name == '':
            raise ProfileContentError(f'Profile {version.version_str()} has empty type name')

        # Parse and correct the named values
        named_values = tuple([Profile._parse_named_value(row, version, profile_corrector, type_name) for row in type_data[1:]])
        named_values = profile_corrector.correct_named_values(named_values)

        # Create and correct the type profile
        type_profile = TypeProfile(type_name, type_data[0][1], len(named_values) > 0, type_data[0][4], named_values)
        type_profile = profile_corrector.correct_type(type_profile)

        # Check that the base type is known
        if type_profile.base_type not in BASE_TYPE_NAME_MAP.keys():
            raise ProfileContentError(f'Profile {version.version_str()} type "{type_profile}" has unknown base type: "{type_profile.base_type}"')

        # Check no duplicate value names
        duplicates = Profile.duplicates([value.name for value in type_profile.values])
        if duplicates:
            Profile._non_fatal_error(f'Profile {version.version_str()} type "{type_profile.name}" has duplicate values names: {duplicates}', strict)

        # Check no duplicate values
        duplicates = Profile.duplicates([value.value for value in type_profile.values])
        if duplicates:
            Profile._non_fatal_error(f'Profile {version.version_str()} in type "{type_profile.name}" has duplicate values: {[str(duplicate) for duplicate in duplicates]}', strict)

        return type_profile

    @staticmethod
    def _parse_types(types_table: DataTable, version: ProfileVersion, profile_corrector: ProfileCorrector, strict: bool) -> Tuple[TypeProfile]:
        """
        Low level function that given the types data will return a tuple of types. It will also perform some consistency checks
        """
        # Check at least one row (the header row)
        if len(types_table) == 0:
            raise ProfileContentError(f'Profile {version.version_str()} has empty types data')

        # Split the contents of the types ignoring the first row which are the headers
        split_types = Profile._split(types_table[1:])

        # parse and correct the types
        types = tuple([Profile._parse_type(type_data, version, profile_corrector, strict) for type_data in split_types])
        types = profile_corrector.correct_types(types)

        # Check for duplicate types
        duplicate_type_names = Profile.duplicates(type_def.name for type_def in types)
        if duplicate_type_names:
            raise ProfileContentError(f'Profile {version.version_str()} has duplicate type names: {duplicate_type_names}')

        return types

    @staticmethod
    def _to_int(row: DataRow, index: int):
        """
        Helper function that will cast a given index of a list into int if it is of type float
        """
        if isinstance(row[index], float):
            row[index] = int(row[index])

        return row

    @staticmethod
    def _if_empty_string(val: str, replacement):
        """
        Helper function that returns a replacement value if the value is an empty string
        """
        if val == '':
            return replacement
        else:
            return val

    @staticmethod
    def _parse_tuple(val: str) -> Union[Tuple[()], Tuple[str]]:
        """
        This function given a string of coma separated values will return a tuple with each value
        the values will be stripped. If the input is '', the result is an empty tuple
        """
        if val == '':
            return ()
        else:
            return tuple([split_val.strip() for split_val in val.split(',')])

    @staticmethod
    def _parse_str_component_value(val: str, num_components: int) -> Union[Tuple[None], Tuple[str]]:
        """
        Given a string and the number of components, this function will return a tuple of length number of
        components that will have the split comma separated string values, or the repeated value or if the
        input was '' a repeated None
        """
        if val == '':
            return (None,) * num_components
        else:
            tmp = Profile._parse_tuple(val)
            if len(tmp) == 1 and len(tmp) != num_components:
                return tmp * num_components
            else:
                return tmp

    @staticmethod
    def _parse_int_component_value(val: Union[str, int, float], num_components: int) -> Union[Tuple[None], Tuple[int]]:
        """
        Given a string and the number of components, this function will return a tuple of length number of
        components that will have the split comma separated int values, or the repeated value or if the
        input was '' a repeated None
        """
        if isinstance(val, float) or isinstance(val, int):
            return (val,) * num_components
        else:
            if val == '':
                return (None,) * num_components
            else:
                tmp = Profile._parse_tuple(val)
                if len(tmp) == 1 and len(tmp) != num_components:
                    return (int(tmp[0]),) * num_components
                else:
                    return tuple([int(v) for v in tmp])

    @staticmethod
    def _parse_bool_component_value(val: Union[str, int, float], num_components: int) -> Union[Tuple[None], Tuple[bool]]:
        """
        Given a string and the number of components, this function will return a tuple of length number of
        components that will have the split comma separated bool values represented as 0 or 1, or the
        repeated value or if the  input was '' a repeated None
        """
        if isinstance(val, bool):
            return (val,) * num_components
        elif isinstance(val, int) or isinstance(val, float):
            return (val == 1,) * num_components
        else:
            if val == '':
                return (None,) * num_components
            else:
                tmp = Profile._parse_tuple(val)
                if len(tmp) == 1 and len(tmp) != num_components:
                    return (int(tmp[0]) == 1,) * num_components
                else:
                    return tuple([int(v) == 1 for v in tmp])

    @staticmethod
    def _parse_message_field(row: DataRow, version: ProfileVersion, profile_corrector: ProfileCorrector, message_name: str) -> MessageFieldProfile:
        if row[1] != '':
            number = int(row[1])
        else:
            number = None
        name = row[2]
        field_type = row[3]
        array = Profile._if_empty_string(row[4], None)

        if row[11] != '' or row[12] != '':
            ref_field_names = Profile._parse_tuple(row[11])
            ref_field_values = Profile._parse_tuple(row[12])
            matchers = tuple([DynamicFieldMatcher(rfn, rfv) for rfn, rfv in zip(ref_field_names, ref_field_values)])
        else:
            matchers = ()

        comment = row[13]
        product = row[14]
        example = row[15]

        components = Profile._if_empty_string(row[5], None)
        if components is not None:
            components = Profile._parse_tuple(components)
            scale = Profile._parse_int_component_value(row[6], len(components))
            offset = Profile._parse_int_component_value(row[7], len(components))
            units = Profile._parse_str_component_value(row[8], len(components))
            bits = Profile._parse_int_component_value(row[9], len(components))
            accumulated = Profile._parse_bool_component_value(row[10], len(components))

            component_profiles = []
            for i in range(0, len(components)):
                component_profiles.append(ComponentProfile(components[i], scale[i], offset[i], units[i], bits[i], accumulated[i]))

            field_profile = MessageComponentFieldProfile(number, name, field_type, array, comment, product, example, matchers, tuple(component_profiles))
        else:
            scale = Profile._if_empty_string(row[6], None)
            offset = Profile._if_empty_string(row[7], None)
            units = Profile._if_empty_string(row[8], None)
            accumulated = Profile._if_empty_string(row[10], False)

            field_profile = MessageScalarFieldProfile(number, name, field_type, array, comment, product, example, matchers, scale, offset, units, accumulated)

        if field_profile.dynamic_field_matchers != ():
            if field_profile.number is not None:
                ProfileContentError(f'Profile {version.version_str()} message "{message_name}" field "{field_profile.name}" has both a field number and a ref_field_name value')

        return profile_corrector.correct_message_field(field_profile)

    @staticmethod
    def _parse_message(message_data: DataTable, version: ProfileVersion, profile_corrector: ProfileCorrector) -> MessageProfile:
        """
        This low level function will return a MessageProfile given a plain data table. The first row should contain the message name
        the following rows should contain the data for the message fields
        """

        # Check non empty message name
        message_name = message_data[0][0]
        if not isinstance(message_name, str) or message_name == '':
            raise ProfileContentError(f'Profile {version.version_str()} has empty type message name')

        # Parse and correct the message fields
        fields = tuple([Profile._parse_message_field(row, version, profile_corrector, message_name) for row in message_data[1:]])
        fields = profile_corrector.correct_message_fields(fields)

        # Construct and correct the message
        message = MessageProfile(message_name, tuple(fields))
        message = profile_corrector.correct_message(message)

        field_names = [inner_field.name for inner_field in message.fields]
        for i in range(0, len(message.fields)):
            field = message.fields[i]
            # Check that the reference fields of the dynamic fields exist
            for marcher in field.dynamic_field_matchers:
                if marcher.ref_field_name not in field_names:
                    raise ProfileContentError(f'Profile {version.version_str()} message "{message.name}" dynamic field "{field.name}" has unknown ref_field_name "{marcher.ref_field_name}"')

            # In case it is a component field, we check that the destination field exists after this field
            if isinstance(field, MessageComponentFieldProfile):
                for component in field.components:
                    if component.destination_field not in field_names:
                        raise ProfileContentError(f'Profile {version.version_str()} message "{message.name}" component field "{field.name}" has unknown destination field "{component.destination_field}"')

        return message

    @staticmethod
    def _extract_data(sheet: xlrd.sheet.Sheet) -> DataTable:
        """
        Helper function that extracts cell values from an xlrd sheet into a plain array
        """

        cols = sheet.ncols
        rows = sheet.nrows
        return [[sheet.cell_value(row, col) for col in range(0, cols)] for row in range(0, rows)]

    @staticmethod
    def _parse_messages(messages_table: DataTable, version: ProfileVersion, profile_corrector: ProfileCorrector) -> Tuple[MessageProfile]:
        """
        This low level function will return a tuple of message profiles given the raw data in the profiles sheet
        """

        # Split the contents of the messages ignoring the first row which are the headers
        split_messages = Profile._split(messages_table[1:])
        messages = [Profile._parse_message(message_data, version, profile_corrector) for message_data in split_messages]
        messages = tuple([profile_corrector.correct_message(message) for message in messages])
        messages = profile_corrector.correct_messages(messages)

        # Check for duplicate messages
        message_names = [message.name for message in messages]
        duplicate_message_types = Profile.duplicates(message_names)
        if duplicate_message_types:
            raise ProfileContentError(f'Profile {version.version_str()} has duplicate message types: {duplicate_message_types}')

        return messages

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
    def _from_tables(types_table: DataTable, messages_table: DataTable, version: ProfileVersion, profile_corrector: ProfileCorrector, strict: bool) -> "Profile":
        """
        Low level function that given plain data corresponding to the profile information will create a profile object
        A profile corrector will correct minor inconsistencies or known issues with the particular profile
        Use strict=True/False to turn certain non fatal inconsistencies in the file into errors/warnings
        """

        types = Profile._parse_types(types_table, version, profile_corrector, strict)
        messages = Profile._parse_messages(messages_table, version, profile_corrector)

        # We find the mesg_num type definition since we know it is an enum like type that contains all the known messages
        mesg_num_profile = None
        for type_def in types:
            if type_def.name == 'mesg_num':
                mesg_num_profile = type_def
                break

        # If there is no mesg_num type, the profile data is inconsistent
        if not mesg_num_profile:
            raise ProfileContentError('The profile does not contain a "mesg_num" type definition')

        # We perform some consistency checks
        message_names = [message.name for message in messages]
        missing_message_type = []
        for value in mesg_num_profile.values:
            if value.name not in message_names:  # If there is no message found
                if value.name not in ['mfg_range_min', 'mfg_range_max']:  # And the name is not one of the manufacturer specific range constants
                    missing_message_type.append(f'{value.name} ({value.value})')  # We add it to the missing messages

        # Issue the errors / warnings
        if missing_message_type:
            error_message = f'Profile {version.version_str()} has an entry in mesg_num for {missing_message_type} but no corresponding message definition'
            Profile._non_fatal_error(error_message, strict)

        # We check for messages that have been defined, but do not have a corresponding entry in mesg_num
        missing_mesg_num_value = []
        for message_name in message_names:
            if message_name not in [value.name for value in mesg_num_profile.values]:
                missing_mesg_num_value.append(message_name)

        # Issue the errors / warnings
        if missing_mesg_num_value:
            error_message = f'Profile {version.version_str()} has message definition for {missing_mesg_num_value} but no corresponding value in mesg_num'
            Profile._non_fatal_error(error_message, strict)

        # Check that all types in message fields are defined
        type_names = [type_profile.name for type_profile in types] + list(BASE_TYPE_NAME_MAP.keys())
        for message in messages:
            for field in message.fields:
                if field.type not in type_names:
                    raise ProfileContentError(f'Profile {version.version_str()} message "{message.name}" field "{field.name}" has undefined type "{field.type}"')

        return profile_corrector.correct_profile(Profile(version, types, messages))

    @staticmethod
    def from_xlsx(file: Union[str, bytes], version: ProfileVersion, profile_corrector: ProfileCorrector = None, strict: bool = True) -> "Profile":
        """
        This high level function will take either the file name or the bytes content of the file and parse the corresponding profile
        See from_tables() for information on the optional arguments
        """

        # obtain the default corrector for the version if not explicitly specified
        if not profile_corrector:
            profile_corrector = DEFAULT_PROFILE_CORRECTOR[version]

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
        return Profile._from_tables(types_table, messages_table, version, profile_corrector, strict)

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
    def from_sdk_zip(file_name: str, profile_corrector: ProfileCorrector = None, strict: bool = True) -> "Profile":
        """
        High level function that given the SDK file will do all the necessary steps to extract a profile
        It is the most convenient way to create a profile object which is later needed to generate the code
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

        # obtain the default corrector for the version if not explicitly specified
        if not profile_corrector:
            profile_corrector = DEFAULT_PROFILE_CORRECTOR[version]

        # Hand over to the profile parser given an xlsx file
        return Profile.from_xlsx(zip_file_content, version, profile_corrector, strict)

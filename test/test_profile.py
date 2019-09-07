# Copyright 2019 Joan Puig
# See LICENSE for details


import pytest

from FIT.profile import Profile, ProfileVersion, ProfileContentError, ProfileContentWarning, DEFAULT_PROFILE_CORRECTOR, ProfileCorrector
from test.test_common import all_sdk_files


def test_duplicates():
    assert not Profile.duplicates(())
    assert not Profile.duplicates([0, 1, 2])
    assert Profile.duplicates([1, 1, 2]) == {1}
    assert Profile.duplicates([1, 1, 2, 3, 3]) == {1, 3}


def test_non_fatal_error():
    with pytest.warns(ProfileContentWarning):
        Profile._non_fatal_error('err', False)

    with pytest.raises(ProfileContentError):
        Profile._non_fatal_error('err', True)


def test_parse_type():
    pv = ProfileVersion.current()
    pc = DEFAULT_PROFILE_CORRECTOR[pv]

    with pytest.raises(ProfileContentError):
        te = Profile._parse_type([], pv, pc, True)

    with pytest.raises(ProfileContentError):
        te = Profile._parse_type([['', '', '', 0.0, 'EMPTY VALUE NAME', 'MORE']], pv, pc, True)

    with pytest.raises(ProfileContentError):
        te = Profile._parse_type([['', '', '', 0.0]], pv, pc, True)

    with pytest.raises(ProfileContentError):
        te = Profile._parse_type([['', '', '', '', '']], pv, pc, True)

    with pytest.raises(ProfileContentError):
        te = Profile._parse_type([['NAME', 'UNKNOWN_BASE_TYPE', '', '', '']], pv, pc, True)

    tt = [
        ['NAME', 'enum', '', '', ''],
        ['', '', 'VALUE_1', 1, 'COMMENT 1'],
        ['', '', 'VALUE_2', 2, 'COMMENT 2']
    ]

    t1 = Profile._parse_type([tt[0]], pv, pc, True)
    assert t1.name == 'NAME'
    assert t1.base_type == 'enum'
    assert len(t1.values) == 0

    t2 = Profile._parse_type(tt, pv, pc, True)
    assert t2.name == 'NAME'
    assert t2.base_type == 'enum'
    assert len(t2.values) == 2
    assert t2.values[0].name == 'VALUE_1'
    assert t2.values[0].value == 1
    assert t2.values[0].comment == 'COMMENT 1'
    assert t2.values[1].name == 'VALUE_2'
    assert t2.values[1].value == 2
    assert t2.values[1].comment == 'COMMENT 2'

    with pytest.raises(ProfileContentError):
        te = Profile._parse_type(tt + [['', '', '', 0, 'EMPTY VALUE NAME']], pv, pc, True)

    with pytest.raises(ProfileContentError):
        te = Profile._parse_type(tt + [['', '', 'VALUE_X', '', 'EMPTY VALUE']], pv, pc, True)

    with pytest.raises(ProfileContentError):
        te = Profile._parse_type(tt + [['', '', 'VALUE_1', 3, 'DUPLICATE VALUE NAME']], pv, pc, True)

    with pytest.raises(ProfileContentError):
        te = Profile._parse_type(tt + [['', '', 'VALUE_X', 1, 'DUPLICATE VALUE']], pv, pc, True)


def test_parse_types():
    pv = ProfileVersion.current()
    pc = DEFAULT_PROFILE_CORRECTOR[pv]

    tt = [
        ['HEADER', '', '', '', ''],
        ['NAME_1', 'enum', '', '', ''],
        ['', '', 'VALUE_1', 1, 'COMMENT 1'],
        ['', '', 'VALUE_2', 2, 'COMMENT 2'],
        ['NAME_2', 'enum', '', '', ''],
        ['', '', 'VALUE_1', 1, 'COMMENT 1'],
        ['', '', 'VALUE_2', 2, 'COMMENT 2']
    ]

    with pytest.raises(ProfileContentError):
        Profile._parse_types([], pv, pc, True)

    assert len(Profile._parse_types([tt[0]], pv, pc, True)) == 0
    assert len(Profile._parse_types(tt[:4], pv, pc, True)) == 1
    assert len(Profile._parse_types(tt, pv, pc, True)) == 2

    with pytest.raises(ProfileContentError):
        te = Profile._parse_type(tt + [['NAME_1', 'enum', '', '', '']], pv, pc, True)


def test_to_int():
    assert Profile._to_int([''], 0) == ['']
    assert Profile._to_int([1.0], 0) == [1]
    assert Profile._to_int(['a', 'b'], 0) == ['a', 'b']
    assert Profile._to_int(['a', 1.0, 'b'], 1) == ['a', 1, 'b']
    assert Profile._to_int(['a', 1.0, 'b'], 0) == ['a', 1.0, 'b']


def test_parse_tuple():
    assert Profile._parse_tuple('') == ()
    assert Profile._parse_tuple('a') == ('a',)
    assert Profile._parse_tuple('ab') == ('ab',)
    assert Profile._parse_tuple('a,b') == ('a', 'b')
    assert Profile._parse_tuple('abc,def,ghi') == ('abc', 'def', 'ghi')


def test_parse_str_component_value():
    assert Profile._parse_str_component_value('', 1) == (None,)
    assert Profile._parse_str_component_value('', 2) == (None, None)
    assert Profile._parse_str_component_value('a', 1) == ('a',)
    assert Profile._parse_str_component_value('a,b,c', 3) == ('a', 'b', 'c')
    assert Profile._parse_str_component_value('a', 3) == ('a', 'a', 'a')


def test_parse_int_component_value():
    assert Profile._parse_int_component_value('', 1) == (None,)
    assert Profile._parse_int_component_value('', 2) == (None, None)
    assert Profile._parse_int_component_value(1, 1) == (1,)
    assert Profile._parse_int_component_value('1,2,3', 3) == (1, 2, 3)
    assert Profile._parse_int_component_value('1', 3) == (1, 1, 1)
    assert Profile._parse_int_component_value(1, 3) == (1, 1, 1)


def test_parse_bool_component_value():
    assert Profile._parse_bool_component_value('', 1) == (None,)
    assert Profile._parse_bool_component_value('', 2) == (None, None)
    assert Profile._parse_bool_component_value(True, 1) == (True,)
    assert Profile._parse_bool_component_value('1,0,1', 3) == (True, False, True)
    assert Profile._parse_bool_component_value('1', 3) == (True, True, True)
    assert Profile._parse_bool_component_value(True, 3) == (True, True, True)


def test_if_empty_string():
    assert Profile._if_empty_string('', 'REP') == 'REP'
    assert Profile._if_empty_string('xyz', 'REP') == 'xyz'


def test_parse_message_field():
    # TODO test
    assert False


def test_parse_message():
    # TODO test
    assert False


def test_extract_data():
    # TODO test
    assert False


def test_parse_messages():
    # TODO test
    assert False


def test_split():
    # TODO test
    assert False


def test_from_tables():
    # TODO test
    assert False


def test_from_xlsx():
    # TODO test
    assert False


def test_sha256():
    # TODO test
    assert False


def test_units():
    # TODO test
    assert False


@pytest.mark.parametrize('file', all_sdk_files())
def test_from_sdk_zip(file: str):
    profile = Profile.from_sdk_zip(file)


def test_profile_corrector():
    # TODO test
    assert False


@pytest.mark.parametrize('profile_corrector', DEFAULT_PROFILE_CORRECTOR.keys())
def test_profile_version_str(profile_corrector: ProfileCorrector):
    assert False

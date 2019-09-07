# Copyright 2019 Joan Puig
# See LICENSE for details


import pytest

from FIT.profile import Profile, ProfileVersion, ProfileContentError, ProfileContentWarning, DEFAULT_PROFILE_CORRECTOR


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

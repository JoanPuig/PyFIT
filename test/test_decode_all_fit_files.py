# Copyright 2019 Joan Puig
# See LICENSE for details


import pytest

from FIT.decoder import Decoder
from test.test_common import all_fit_files


@pytest.mark.parametrize('file', all_fit_files())
def test_decode_all_fit_file(file: str):
    Decoder.decode_fit_file(file)
    assert True

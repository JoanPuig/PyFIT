# Copyright 2019 Joan Puig
# See LICENSE for details


import pytest

from FIT.decoder import Decoder
from test.test_common import sample_fit_files


@pytest.mark.parametrize('file', sample_fit_files())
def test_decode_sample_fit_file(file: str):
    Decoder.decode_fit_file(file)
    assert True

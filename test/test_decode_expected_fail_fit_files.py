# Copyright 2019 Joan Puig
# See LICENSE for details


import pytest

from FIT.decoder import Decoder, FITFileContentError
from test.test_common import expected_fail_fit_files


@pytest.mark.parametrize('file', expected_fail_fit_files())
@pytest.mark.xfail(raises=FITFileContentError)
def test_decode_expected_fail_fit_file(file: str):
    Decoder.decode_fit_file(file)

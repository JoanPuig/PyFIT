# Copyright 2019 Joan Puig
# See LICENSE for details


import importlib
import pytest

from test.test_common import files


@pytest.mark.parametrize('example_file', files('./examples/', '.py'))
def test_example(example_file: str):
    mod = importlib.import_module('.' + example_file[11:-3], 'examples')
    mod.main()

    assert True

# Copyright 2019 Joan Puig
# See LICENSE for details


import os

import pytest

from FIT.decoder import ByteReader, Decoder


def fit_files():
    # Modify to fit your directory setup
    fit_files_dir = './data/FIT/'

    files = []
    for file in os.listdir(fit_files_dir):
        if file.lower().endswith("0.fit"):
            files.append(os.path.join(fit_files_dir, file))

    return files


@pytest.mark.parametrize('file', fit_files())
def test_decode_fit_file(file: str):
    # Reads the binary data of the .FIT file
    file_bytes = open(file, "rb").read()

    # Constructs a ByteReader and Decoder object
    byte_reader = ByteReader(file_bytes)
    decoder = Decoder(byte_reader)

    # Decodes the file
    fit_file = decoder.decode_file()

    assert True

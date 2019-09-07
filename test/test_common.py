# Copyright 2019 Joan Puig
# See LICENSE for details


import os
from typing import List


# Modify to fit your directory setup
FIT_FILES_PATH = './data/FIT/'
SDK_FILES_PATH = './data/SDK/'


def files(files_dir: str, extension: str) -> List[str]:
    file_names = []
    for file in os.listdir(files_dir):
        if file.lower().endswith(extension.lower()):
            file_names.append(os.path.join(files_dir, file))
    return file_names


def fit_files(fit_files_dir: str) -> List[str]:
    return files(fit_files_dir, '.fit')


def all_fit_files() -> List[str]:
    return fit_files(FIT_FILES_PATH + 'all/')


def sample_fit_files() -> List[str]:
    return fit_files(FIT_FILES_PATH + 'sample/')


def expected_fail_fit_files() -> List[str]:
    return fit_files(FIT_FILES_PATH + 'expected_fail/')


def all_sdk_files() -> List[str]:
    return files(SDK_FILES_PATH, '.zip')

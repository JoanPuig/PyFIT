# Copyright 2019 Joan Puig
# See LICENSE for details


import os
from typing import List

# Modify to fit your directory setup
FIT_FILES_PATH = './data/FIT/'


def files(files_dir: str, extension: str) -> List[str]:
    files = []
    for file in os.listdir(files_dir):
        if file.lower().endswith(extension):
            files.append(os.path.join(files_dir, file))
    return files


def fit_files(fit_files_dir: str) -> List[str]:
    return files('.fit')


def all_fit_files() -> List[str]:
    return fit_files(FIT_FILES_PATH + 'all/')


def sample_fit_files() -> List[str]:
    return fit_files(FIT_FILES_PATH + 'sample/')

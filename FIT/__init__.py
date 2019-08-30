# Copyright 2019 Joan Puig
# See LICENSE for details


from typing import List, Set


def duplicates(elements: List) -> Set:
    s = set()
    return set(element for element in elements if element in s or s.add(element))


import re

V1_PREFIX = "LA"

VALUE_TO_SUBTRACT = 45
MODULO = 28
CHECKSUM_STRING = "0123456789ABCEFGHJKMNPRTUVWXY"

"""
The implemenetation below is based on the documents  New Lasrra 2.0 Number Format Checksum.xlsx (for v2) 
and LASRRA Number format checksum.xlsx (for v1) 

"""


def _generate_lasrra_id_checksum_v2(id: str) -> str:
    total_weighted_sum = 0

    for i, ch in enumerate(id[:-1]):
        current_weight = ord(ch) - VALUE_TO_SUBTRACT
        if (i + 1) % 2 == 0:
            current_weight *= 2
        total_weighted_sum += current_weight

    checksum_string_idx = MODULO - (total_weighted_sum % MODULO)
    return CHECKSUM_STRING[checksum_string_idx]


def _generate_lasrra_id_checksum_v1(id: str) -> str:
    sequential_portion = id[-7:-1]
    total_sum = 0
    for i, ch in enumerate(sequential_portion):
        total_sum += int(ch)

    if total_sum < 10:
        return CHECKSUM_STRING[total_sum]

    return CHECKSUM_STRING[int(str(total_sum)[0])]


def _validate_lasrra_id(id: str, version: int) -> str:
    assert version in [1, 2]
    if version == 1:
        checksum_generation_func = _generate_lasrra_id_checksum_v1
    else:
        checksum_generation_func = _generate_lasrra_id_checksum_v2

    if checksum_generation_func(id) != id[-1]:
        raise ValueError("invalid lasrra id format")
    return id


def _detect_id_version(id: str) -> int:
    version = 1 if id[0:2] == V1_PREFIX else 2
    return version


def validate_lasrra_id(id: str) -> str:
    return _validate_lasrra_id(id, _detect_id_version(id))

import re

PHONE_NUMBER_REGEX = re.compile("^[0-9]{9,11}$")


def validate_phone_number(phone_number: str) -> str:
    phone_number = "".join([ch for ch in phone_number if ch != " "])
    is_valid_phone_number = bool(PHONE_NUMBER_REGEX.match(phone_number))

    if not is_valid_phone_number:
        raise ValueError("invalid phone number")
    return phone_number

from collections import namedtuple

import pytest
from backend.app.services.validators import phone


@pytest.mark.parametrize(
    ("phone_number", "is_valid"),
    [
        ("08034300000", True),
        ("08000000000", True),
        ("01 975 2222", True),
        ("0708XYZABCD", False),
        ("0708XY", False),
        ("07O221i21", False),
    ],
)
def test_phone_number_validation(phone_number: str, is_valid: bool):
    if not is_valid:
        with pytest.raises(ValueError):
            phone.validate_phone_number(phone_number)
    else:
        assert phone.validate_phone_number(phone_number) == "".join(
            ch for ch in phone_number if ch != " "
        )

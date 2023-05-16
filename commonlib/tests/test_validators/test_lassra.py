from collections import namedtuple

import pytest
from commonlib.validators import lasrra

LasrraID = namedtuple("LasrraId", ["id", "version", "is_valid"])

LASRRA_IDS = [
    LasrraID("LA3420001304", 1, True),
    LasrraID("LA0100010631", 1, True),
    LasrraID("LA0320002221", 1, False),
    LasrraID("LA123456789", 1, False),
    LasrraID("LG156000200X", 2, True),
    LasrraID("LG1KIAOOQOWO", 2, False),
    LasrraID("LG1KIAOOQOWO", 2, False),
    LasrraID("LG1560002360", 2, False),
    LasrraID("LG156000239C", 2, True),
]


@pytest.mark.parametrize("lasrra_id", LASRRA_IDS)
def test_validates_lasrra_ids_correctly(lasrra_id: LasrraID):
    if not lasrra_id.is_valid:
        with pytest.raises(ValueError):
            lasrra.validate_lasrra_id(lasrra_id.id)
    else:
        assert lasrra.validate_lasrra_id(lasrra_id.id) == lasrra_id.id


@pytest.mark.parametrize("lasrra_id", LASRRA_IDS)
def test_detect_lasrra_id_version_correctly(lasrra_id: LasrraID):
    assert lasrra_id.version == lasrra._detect_id_version(lasrra_id.id)

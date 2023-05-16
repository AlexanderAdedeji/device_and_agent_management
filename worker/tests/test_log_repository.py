from datetime import date, datetime, timedelta
from logging import log
from bson.objectid import ObjectId
import pytest
from worker.db.repositories.log import log_repository
from worker.db.models.log import Log

from random import randint


def test_create_log():
    current_datetime = datetime.now()
    log_id = log_repository.create(
        obj_in=Log(
            user_id=randint(0, 1 << 16),
            device_id=randint(0, 1 << 16),
            log_class="USER_LOG_IN",
            level="INFO",
            extra_data={"ip": "114.123.84.196"},
            logged_at=current_datetime,
            generated_at=current_datetime,
        )
    )

    assert isinstance(log_id, ObjectId)

    log = log_repository.get(object_id=str(log_id))

    assert log.log_class == "USER_LOG_IN"
    assert log.level == "INFO"
    assert "ip" in log.extra_data

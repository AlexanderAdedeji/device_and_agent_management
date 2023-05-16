from typing import Any, Dict
from pydantic import BaseModel
from datetime import datetime
from db.client import database
from pymongo import ASCENDING, DESCENDING


class Base(BaseModel):
    @classmethod
    def __collectionname__(cls):
        return cls.__name__.lower()


class Log(Base):
    user_id: int
    device_id: int
    log_class: str
    level: str
    extra_data: Any
    logged_at: datetime


database[Log.__collectionname__()].create_index([("device_id", ASCENDING)])
database[Log.__collectionname__()].create_index([("user_id", ASCENDING)])

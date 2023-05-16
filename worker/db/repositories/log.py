from typing import List
from db.repositories.base import Base
from db.models.log import Log
from db.client import database
from datetime import datetime


class LogRepository(Base[Log]):
    pass


log_repository = LogRepository(database, Log)

from typing import List
from starlette.config import Config
from pathlib import Path
from starlette.datastructures import CommaSeparatedStrings


config = Config(Path(__file__).parent / ".env")

MONGO_DB_URI = config("MONGO_DB_URI")

MONGO_DB_NAME = config("MONGO_DB_NAME")

RABBIT_MQ_URI = config("RABBIT_MQ_URI")

RABBIT_MQ_ROUTING_KEYS: List[str] = list(
    config("RABBIT_MQ_ROUTING_KEYS", cast=CommaSeparatedStrings)
)

RABBIT_MQ_EXCHANGE_NAME: str = config("RABBIT_MQ_EXCHANGE_NAME")

RABBIT_MQ_EXCHANGE_TYPE: str = config("RABBIT_MQ_EXCHANGE_TYPE")


DEFAULT_RABBIT_MQ_CONNECTION_RETRY_SECONDS: int = config(
    "DEFAULT_RABBIT_MQ_CONNECTION_RETRY_SECONDS", cast=int, default=10
)

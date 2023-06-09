from typing import Callable

from fastapi import FastAPI

from backend.app.db.utils import close_db_connection, connect_to_db


START_EVENT = "startup"

SHUTDOWN_EVENT = "shutdown"


def create_start_app_handler(app: FastAPI) -> Callable:  # type: ignore
    async def start_app() -> None:
        await connect_to_db(app)

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:  # type: ignore
    async def stop_app() -> None:
        await close_db_connection(app)

    return stop_app

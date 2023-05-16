from backend.app.api.routes.routes import router as global_router
from backend.app.core.settings import settings
from commonlib.errors.db_error_handlers import db_error_handler
from commonlib.errors.http_error_handlers import (
    generic_http_error_handler,
    http422_error_handler,
)
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from loguru import logger
from pydantic import ValidationError
from requests.sessions import Request
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

PROJECT_NAME = settings.PROJECT_NAME
ALLOWED_HOSTS = settings.ALLOWED_HOSTS
DEBUG = settings.DEBUG
VERSION = settings.VERSION
API_URL_PREFIX = settings.API_URL_PREFIX
origins = [
    "http://localhost:3000",
    "http://172.16.2.74:8899",
    "http://172.16.2.74"

 
]

from backend.app.core.events import (
    SHUTDOWN_EVENT,
    START_EVENT,
    create_start_app_handler,
    create_stop_app_handler,
)


def create_application_instance() -> FastAPI:
    application = FastAPI(title=PROJECT_NAME, debug=DEBUG, version="0.1")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for event, handler in [
        (START_EVENT, create_start_app_handler(application)),
        (SHUTDOWN_EVENT, create_stop_app_handler(application)),
    ]:
        application.add_event_handler(event_type=event, func=handler)

    for exception, handler in [
        (HTTPException, generic_http_error_handler),
        (RequestValidationError, http422_error_handler),
        (ValidationError, http422_error_handler),
        (IntegrityError, db_error_handler),
    ]:
        application.add_exception_handler(exception, handler)

    application.include_router(global_router, prefix=API_URL_PREFIX)

    return application


app = create_application_instance()


@app.exception_handler(Exception)
async def base_exception_handler(_, exc: Exception):
    logger.error(exc)
    return JSONResponse(
        {"message": "Something went wrong"}, status_code=HTTP_500_INTERNAL_SERVER_ERROR
    )

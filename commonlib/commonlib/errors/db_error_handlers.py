from sqlalchemy.exc import IntegrityError
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST

DEBUG = False


def db_error_handler(
    _: Request,
    exc: IntegrityError,
) -> JSONResponse:
    detail = exc.detail if exc.detail else "an error occured."
    debug_detail = exc._message() if DEBUG else None

    return JSONResponse(
        {"errors": [{"message": detail, "debug_detail": debug_detail}]},
        status_code=HTTP_400_BAD_REQUEST,
    )

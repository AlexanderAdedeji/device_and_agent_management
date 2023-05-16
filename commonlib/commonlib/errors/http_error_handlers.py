from typing import Union

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.constants import REF_PREFIX
from fastapi.openapi.utils import validation_error_response_definition
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY


def generic_http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        {"errors": [{"message": exc.detail}]}, status_code=exc.status_code
    )


def http422_error_handler(
    _: Request,
    exc: Union[RequestValidationError, ValidationError],
) -> JSONResponse:
    try:
        errors = []
        for error in exc.errors():
            if len(error["loc"]) > 1:
                _, identifier = error["loc"]
            else:
                identifier = error["loc"][0]
            message = error["msg"]
            errors.append({"message": " - ".join([identifier, message])})
        return JSONResponse(
            {"errors": errors}, status_code=HTTP_422_UNPROCESSABLE_ENTITY
        )
    except Exception as e:
        return JSONResponse(
            {"errors": exc.errors()},
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        )


validation_error_response_definition["properties"] = {
    "errors": {
        "title": "Errors",
        "type": "array",
        "items": {"$ref": "{0}ValidationError".format(REF_PREFIX)},
    },
}

import pytest
from fastapi import FastAPI, testclient
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from commonlib.errors.http_error_handlers import (
    generic_http_error_handler,
    http422_error_handler,
)


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI(title="Test API", debug=True)
    app.add_exception_handler(HTTPException, generic_http_error_handler)
    app.add_exception_handler(RequestValidationError, http422_error_handler)

    return app


@pytest.fixture
def client(app: FastAPI) -> testclient.TestClient:
    c = testclient.TestClient(app)
    return c

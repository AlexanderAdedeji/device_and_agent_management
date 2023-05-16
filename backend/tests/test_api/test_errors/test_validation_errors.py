import pytest
from backend.app.main import app
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

pytestmark = pytest.mark.asyncio


def test_validation_error_format(client: TestClient):
    @app.get("/{n}/{x}")
    def test_route(n: int, x: int) -> None:
        pass

    response = client.get("/notaninteger/yetnotaninteger")
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY

    error_data = response.json()
    assert "errors" in error_data

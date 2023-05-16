import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.status import HTTP_404_NOT_FOUND
from backend.app.main import app

pytestmark = pytest.mark.asyncio


def test_http_error_format(client: TestClient) -> None:
    response = client.get("/nonexistentpath")
    assert response.status_code == HTTP_404_NOT_FOUND

    error_data = response.json()
    assert "errors" in error_data

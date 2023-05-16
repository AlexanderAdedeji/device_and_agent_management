import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY


def test_http_error_format(client: TestClient) -> None:
    response = client.get("/nonexistentpath")
    assert response.status_code == HTTP_404_NOT_FOUND

    error_data = response.json()
    assert "errors" in error_data


def test_validation_error_format(app: FastAPI, client: TestClient):
    @app.get("/{param}")
    def test_route(param: int) -> None:
        pass

    response = client.get("/notaninteger")
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY

    error_data = response.json()
    assert "errors" in error_data

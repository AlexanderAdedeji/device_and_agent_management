import pytest
from backend.app.core.settings import settings
from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN

FIRST_SUPERUSER_EMAIL = settings.FIRST_SUPERUSER_EMAIL
FIRST_SUPERUSER_PASSWORD = settings.FIRST_SUPERUSER_PASSWORD


def test_get_currently_authenticated_user_with_valid_token(client: TestClient) -> None:
    login_data = {"email": FIRST_SUPERUSER_EMAIL, "password": FIRST_SUPERUSER_PASSWORD}

    r = client.post("/api/auth/login", json=login_data)
    body = r.json()
    assert r.status_code == HTTP_200_OK
    assert "token" in body
    token = body["token"]

    r = client.get("/api/users/me", headers={"Authorization": "Token {}".format(token)})

    assert r.status_code == HTTP_200_OK


def test_get_currently_authenticated_user_with_invalid_token(
    client: TestClient,
) -> None:
    login_data = {"email": FIRST_SUPERUSER_EMAIL, "password": FIRST_SUPERUSER_PASSWORD}

    r = client.post("/api/auth/login", json=login_data)
    body = r.json()
    assert r.status_code == HTTP_200_OK
    assert "token" in body
    token = body["token"]

    r = client.get(
        "/api/users/me", headers={"Authorization": "Token {}".format(token[::-1])}
    )

    assert r.status_code == HTTP_403_FORBIDDEN
    assert "errors" in r.json()


def test_get_currently_authenticated_user_with_malformed_header(
    client: TestClient,
) -> None:
    login_data = {"email": FIRST_SUPERUSER_EMAIL, "password": FIRST_SUPERUSER_PASSWORD}

    r = client.post("/api/auth/login", json=login_data)
    body = r.json()
    assert r.status_code == HTTP_200_OK
    assert "token" in body
    token = body["token"]

    r = client.get(
        "/api/users/me",
        headers={"WrongHeaderAuthorization": "Token {}".format(token[::-1])},
    )

    assert r.status_code == HTTP_403_FORBIDDEN
    assert "errors" in r.json()

    r = client.get(
        "/api/users/me",
        # JWT as header prefix instead of 'Token'
        headers={"Authorization": "JWT {}".format(token[::-1])},
    )

    assert r.status_code == HTTP_403_FORBIDDEN
    assert "errors" in r.json()

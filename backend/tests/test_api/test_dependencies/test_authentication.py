import pytest
from sqlalchemy.orm.session import Session
from backend.app.api.dependencies.authentication import (
    _extract_jwt_from_header,
    get_currently_authenticated_user,
)
from backend.app.api.errors.exceptions import InvalidTokenException
from backend.app.core.settings import settings
from backend.app.db.session import SessionLocal
from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK

FIRST_SUPERUSER_EMAIL = settings.FIRST_SUPERUSER_EMAIL
FIRST_SUPERUSER_PASSWORD = settings.FIRST_SUPERUSER_PASSWORD


def test__extract_jwt_from_header_on_header_with_wrong_prefix():
    invalid_header_string = "JWT sample-jwt"
    with pytest.raises(InvalidTokenException):
        _extract_jwt_from_header(invalid_header_string)


def test__extract_jwt_from_header_on_header_with_no_prefix():
    invalid_header_string = "sample-jwt"
    with pytest.raises(InvalidTokenException):
        _extract_jwt_from_header(invalid_header_string)


def test_get_currently_authenticated_user_when_token_is_invalid():
    invalid_token = "some invalid token"
    with pytest.raises(InvalidTokenException):
        get_currently_authenticated_user(token=invalid_token)


def test_get_currently_authenticated_user_with_valid_token(client: TestClient,db: Session):
    login_data = {"email": FIRST_SUPERUSER_EMAIL, "password": FIRST_SUPERUSER_PASSWORD}
    r = client.post("/api/auth/login", json=login_data)

    body = r.json()
    assert r.status_code == HTTP_200_OK
    assert "token" in body
    token = body["token"]

    user = get_currently_authenticated_user(db=SessionLocal(), token=token)
    assert user
    assert user.email == body["email"]

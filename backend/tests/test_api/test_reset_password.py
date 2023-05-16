from datetime import timedelta
from backend.app.core.settings import settings
from backend.tests.utils import create_agent_user
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN

FIRST_SUPERUSER_EMAIL = settings.FIRST_SUPERUSER_EMAIL
FIRST_SUPERUSER_PASSWORD = settings.FIRST_SUPERUSER_PASSWORD


def test_reset_password_flow(client: TestClient, db: Session) -> None:
    user = create_agent_user(db)

    r = client.get("/api/users/reset_password/{}".format(user.email))
    assert r.status_code == HTTP_200_OK

    reset_token = user.generate_password_reset_token(db)

    assert reset_token
    assert reset_token.id

    body = {"token": reset_token.token, "password": "newpassword"}
    r = client.post("/api/users/reset_password/", json=body)

    assert r.status_code == HTTP_200_OK
    assert "message" in r.json()

    r = client.post(
        "/api/auth/login", json={"email": user.email, "password": "newpassword"}
    )

    assert r.status_code == HTTP_200_OK
    assert "token" in r.json()


def test_reset_password_with_invalid_token(client: TestClient, db: Session) -> None:
    body = {"token": "some invalid token", "password": "newpassword"}
    r = client.post("/api/users/reset_password/", json=body)

    assert r.status_code == HTTP_403_FORBIDDEN
    assert "errors" in r.json()


def test_reset_password_with_expired_token(client: TestClient, db: Session) -> None:
    user = create_agent_user(db)
    reset_token = user.generate_password_reset_token(db, expires_delta=timedelta(0))
    assert reset_token

    body = {"token": reset_token.token, "password": "newpassword"}
    r = client.post("/api/users/reset_password/", json=body)
    assert r.status_code == HTTP_403_FORBIDDEN


def test_reset_password_with_used_token(client: TestClient, db: Session) -> None:
    user = create_agent_user(db)
    reset_token = user.generate_password_reset_token(db)

    assert reset_token

    body = {"token": reset_token.token, "password": "newpassword"}
    r = client.post("/api/users/reset_password/", json=body)
    assert r.status_code == HTTP_200_OK

    db.refresh(reset_token)
    assert reset_token.used

    r = client.post("/api/users/reset_password/", json=body)
    assert r.status_code == HTTP_403_FORBIDDEN

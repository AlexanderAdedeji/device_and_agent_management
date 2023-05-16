from typing import Dict

import pytest
from backend.app.core.settings import settings
from backend.app.db.repositories.user import user_repo
from backend.tests.utils import (
    create_agent_employee_user,
    create_agent_user,
    get_agent_employee_user,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)

AgentEmployeeUser = settings.AgentEmployeeUser
FIRST_SUPERUSER_EMAIL = settings.FIRST_SUPERUSER_EMAIL
FIRST_SUPERUSER_PASSWORD = settings.FIRST_SUPERUSER_PASSWORD


def test_get_access_token_with_valid_credentials(client: TestClient) -> None:
    login_data = {"email": FIRST_SUPERUSER_EMAIL, "password": FIRST_SUPERUSER_PASSWORD}

    r = client.post("/api/auth/login", json=login_data)
    body = r.json()
    assert r.status_code == HTTP_200_OK
    assert "token" in body
    assert body["token"]


def test_get_access_token_with_inactive_user_fails(db: Session, client: TestClient):
    user = create_agent_user(db)
    user = user_repo.update(
        db, db_obj=user, obj_in={"password": "password", "is_active": False}
    )
    assert not user.is_active

    login_data = {"email": user.email, "password": "password"}

    r = client.post("/api/auth/login", json=login_data)

    assert r.status_code == HTTP_401_UNAUTHORIZED


def test_get_access_token_with_nonsuperuser_or_agent_fails(client: TestClient):
    login_data = {
        "email": AgentEmployeeUser.EMAIL,
        "password": AgentEmployeeUser.PASSWORD,
    }

    r = client.post("/api/auth/login", json=login_data)

    assert r.status_code == HTTP_403_FORBIDDEN


def test_get_access_token_with_wrong_credentials(client: TestClient):
    login_data = {"email": FIRST_SUPERUSER_EMAIL, "password": "wrong"}

    r = client.post("/api/auth/login", json=login_data)
    body = r.json()
    assert r.status_code == HTTP_401_UNAUTHORIZED
    assert "errors" in body
    assert body["errors"]


#  docker-compose -f docker-compose-dev.yml run --publish 6543:5432 database

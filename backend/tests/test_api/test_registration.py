import pytest
from backend.app.core.settings import settings
from fastapi.testclient import TestClient
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_201_CREATED,
    HTTP_403_FORBIDDEN,
)
from backend.tests.utils import (
    generate_header_from_user_obj,
    get_default_agent_employee_user,
    get_default_agent_user,
    get_default_superuser,
    random_email,
    random_phone,
    random_string,
    random_lasrra_id,
    generate_user_payload,
)
from sqlalchemy.orm import Session
from backend.app.db.repositories.user import user_repo

from backend.tests.utils import get_superuser_auth_header


AGENT_EMPLOYEE_TYPE = settings.AGENT_EMPLOYEE_TYPE
AGENT = settings.AGENT
FIRST_SUPERUSER_EMAIL = settings.FIRST_SUPERUSER_EMAIL


def test_superuser_can_create_agent_user(client: TestClient, db: Session):
    data = generate_user_payload()
    r = client.post(
        "/api/users/create_agent_user", json=data, headers=get_superuser_auth_header(db)
    )
    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    created_user = r.json()
    assert created_user["email"] == data["email"]
    user = user_repo.get_by_email(db, email=data["email"])
    assert user
    assert user.user_type.name == AGENT


def test_agent_can_not_create_another_agent(client: TestClient, db: Session):
    data = generate_user_payload()
    r = client.post(
        "/api/users/create_agent_user",
        json=data,
        headers=generate_header_from_user_obj(get_default_agent_user(db)),
    )
    assert r.status_code == HTTP_403_FORBIDDEN
    assert "errors" in r.json()
    user = user_repo.get_by_email(db, email=data["email"])
    assert not user


def test_agent_employee_can_not_create_another_agent(client: TestClient, db: Session):
    data = generate_user_payload()
    r = client.post(
        "/api/users/create_agent_user",
        json=data,
        headers=generate_header_from_user_obj(get_default_agent_employee_user(db)),
    )
    assert r.status_code == HTTP_403_FORBIDDEN
    assert "errors" in r.json()
    user = user_repo.get_by_email(db, email=data["email"])
    assert not user


def test_agent_can_create_agent_employee_user(client: TestClient, db: Session):
    data = generate_user_payload()
    agent_user = get_default_agent_user(db)
    r = client.post(
        "/api/users/create_agent_employee_user",
        json={**data, "agent_id": agent_user.id},
        headers=generate_header_from_user_obj(agent_user),
    )
    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    created_user = r.json()
    assert created_user["email"] == data["email"]
    user = user_repo.get_by_email(db, email=data["email"])
    assert user
    assert user.user_type.name == AGENT_EMPLOYEE_TYPE
    assert user.agent is agent_user


def test_agent_employee_can_not_create_another_agent_employee(
    client: TestClient, db: Session
):
    data = generate_user_payload()
    r = client.post(
        "/api/users/create_agent_employee_user",
        json=data,
        headers=generate_header_from_user_obj(get_default_agent_employee_user(db)),
    )
    assert r.status_code == HTTP_403_FORBIDDEN


def test_create_agent_user_with_existing_email(client: TestClient, db: Session) -> None:
    data = generate_user_payload()

    r = client.post(
        "/api/users/create_agent_user", json=data, headers=get_superuser_auth_header(db)
    )

    r = client.post(
        "/api/users/create_agent_user", json=data, headers=get_superuser_auth_header(db)
    )

    assert r.status_code == HTTP_400_BAD_REQUEST

    assert "errors" in r.json()


def test_created_user_stores_creator_info(client: TestClient, db: Session):
    data = generate_user_payload()

    user_creator = get_default_superuser(db)

    r = client.post(
        "/api/users/create_agent_user",
        json=data,
        headers=generate_header_from_user_obj(user_creator),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    response_body = r.json()
    assert response_body["email"] == data["email"]

    user_created = user_repo.get(db, id=response_body["id"])

    assert user_created

    assert user_created.created_by_id == user_creator.id


def test_created_agent_user_stores_agent_id(client: TestClient, db: Session):
    data = generate_user_payload()
    user_creator = user_repo.get_by_email(db, email=FIRST_SUPERUSER_EMAIL)

    r = client.post(
        "/api/users/create_agent_employee_user",
        json={**data, "agent_id": user_creator.id},
        headers=generate_header_from_user_obj(user_creator),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    response_body = r.json()
    assert response_body["email"] == data["email"]

    created_user = user_repo.get(db, id=response_body["id"])

    assert created_user
    assert created_user.agent_id == user_creator.id


#  docker-compose -f docker-compose-dev.yml run --publish 6543:5432 database
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_422_UNPROCESSABLE_ENTITY,
)
from backend.tests.utils import (
    generate_header_from_user_obj,
    get_agent_employee_user,
    get_default_agent_user,
    get_default_superuser,
    random_string,
)
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import Session

from backend.app.db.repositories.device import device_repo


def test_create_device_as_agent(db: Session, client: TestClient):
    user = get_default_agent_user(db)
    device_data = {"mac_id": random_string(), "agent_id": user.id}
    r = client.post(
        "/api/devices/", json=device_data, headers=generate_header_from_user_obj(user)
    )
    resp_body = r.json()

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED
    assert "id" in resp_body
    assert "mac_id" in resp_body
    assert "creator_id" in resp_body
    assert len(resp_body["assigned_users"]) == 0

    device = device_repo.get(db, id=resp_body["id"])
    assert device
    assert device.agent_id == user.id


def test_create_device_as_superuser_but_assign_to_agent(
    db: Session, client: TestClient
):
    agent_user = get_default_agent_user(db)
    superuser = get_default_superuser(db)

    device_data = {"mac_id": random_string(), "agent_id": agent_user.id}
    r = client.post(
        "/api/devices/",
        json=device_data,
        headers=generate_header_from_user_obj(superuser),
    )

    resp_body = r.json()

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED
    assert "id" in resp_body
    assert "mac_id" in resp_body
    assert "creator_id" in resp_body
    assert len(resp_body["assigned_users"]) == 0

    device = device_repo.get(db, id=resp_body["id"])
    assert device
    assert device.agent_id == agent_user.id


def test_create_device_without_agent_id_fails(db: Session, client: TestClient):
    user = get_default_agent_user(db)
    device_data = {"mac_id": random_string()}
    r = client.post(
        "/api/devices/", json=device_data, headers=generate_header_from_user_obj(user)
    )

    assert r.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_create_device_as_agent_employee_is_forbidden(db: Session, client: TestClient):
    agent_employee = get_agent_employee_user(db)
    device_data = {"mac_id": random_string(), "agent_id": agent_employee.id}
    r = client.post(
        "/api/devices/",
        json=device_data,
        headers=generate_header_from_user_obj(agent_employee),
    )

    assert r.status_code == HTTP_403_FORBIDDEN
    assert "errors" in r.json()


def test_create_device_without_credentials(db: Session, client: TestClient):
    device_data = {"mac_id": random_string()}
    r = client.post(
        "/api/devices/",
        json=device_data,
    )

    assert r.status_code == HTTP_403_FORBIDDEN
    assert "errors" in r.json()


def test_create_device_with_existing_mac_id_raises_400(db: Session, client: TestClient):

    user = get_default_agent_user(db)
    device_data = {"mac_id": random_string(), "agent_id": user.id}

    r = client.post(
        "/api/devices/", json=device_data, headers=generate_header_from_user_obj(user)
    )

    assert r.status_code == HTTP_200_OK

    r = client.post(
        "/api/devices/", json=device_data, headers=generate_header_from_user_obj(user)
    )

    assert r.status_code == HTTP_400_BAD_REQUEST
    assert "errors" in r.json()
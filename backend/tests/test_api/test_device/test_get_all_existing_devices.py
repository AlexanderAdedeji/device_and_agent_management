from backend.app.schemas.device import DeviceCreate
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_403_FORBIDDEN
from backend.tests.utils import (
    generate_header_from_user_obj,
    get_default_agent_user,
    get_default_superuser,
    random_string,
)
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import Session
from backend.app.db.repositories.device import device_repo


def test_get_all_existing_devices_as_superuser(db: Session, client: TestClient):
    user = get_default_superuser(db)
    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=user.id, agent_id=user.id
        ),
    )
    assert device

    r = client.get("/api/devices/", headers=generate_header_from_user_obj(user))
    resp_body = r.json()

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED
    assert isinstance(resp_body, list)
    assert resp_body
    assert resp_body[0]
    assert "id" in resp_body[0]
    assert "mac_id" in resp_body[0]


def test_get_all_existing_devices_as_agent(db: Session, client: TestClient):
    user = get_default_agent_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=user.id, agent_id=user.id
        ),
    )
    assert device

    r = client.get("/api/devices/", headers=generate_header_from_user_obj(user))
    resp_body = r.json()

    assert r.status_code == HTTP_403_FORBIDDEN
    assert "errors" in resp_body


def test_get_all_existing_devices_without_credentials(db: Session, client: TestClient):
    r = client.get("/api/devices/")
    resp_body = r.json()

    assert r.status_code == HTTP_403_FORBIDDEN
    assert "errors" in resp_body

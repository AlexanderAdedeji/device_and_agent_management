from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from tests.utils import (
    create_agent_employee_user,
    get_default_agent_user,
)
from backend.app.db.repositories.device import device_repo
from backend.app.schemas.device import DeviceConfig, DeviceCreate, DeviceMetaData
from backend.tests.utils import random_string
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from unittest import mock


def test_get_device_metadata_returns_valid_metadata(client: TestClient, db: Session):
    agent_user = get_default_agent_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(10), creator_id=agent_user.id, agent_id=agent_user.id
        ),
    )

    device = device_repo.activate_device(db, device_obj=device)

    assert device
    assert device.is_active

    users_to_assign = [create_agent_employee_user(db), create_agent_employee_user(db)]
    device_repo.add_assigned_users(db, device_obj=device, user_objs=users_to_assign)

    r = client.get("/api/devices/{}/metadata".format(device.mac_id))

    assert r.status_code == HTTP_200_OK
    response_body = r.json()

    created_device_metadata = DeviceMetaData(**response_body)

    assert created_device_metadata
    assert len(created_device_metadata.assigned_users) == len(users_to_assign)
    assert created_device_metadata.agent.id == agent_user.id


def test_get_device_config_with_invalid_mac_id_gives_404(
    client: TestClient, db: Session
):
    r = client.get("/api/devices/config/{}".format(random_string()))

    assert r.status_code == HTTP_404_NOT_FOUND


def test_get_device_config_with_inactive_device_gives_403(
    client: TestClient, db: Session
):
    agent_user = get_default_agent_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(10), creator_id=agent_user.id, agent_id=agent_user.id
        ),
    )

    device = device_repo.activate_device(db, device_obj=device)

    assert device
    assert device.is_active
    users_to_assign = [create_agent_employee_user(db), create_agent_employee_user(db)]
    device_repo.add_assigned_users(db, device_obj=device, user_objs=users_to_assign)

    r = client.get("/api/devices/{}/metadata".format(device.mac_id))

    assert r.status_code == HTTP_200_OK
    response_body = r.json()

    created_device_metadata = DeviceMetaData(**response_body)

    assert created_device_metadata
    assert len(created_device_metadata.assigned_users) == len(users_to_assign)
    assert created_device_metadata.agent.id == agent_user.id

    device = device_repo.deactivate_device(db, device_obj=device)
    assert not device.is_active

    r = client.get("/api/devices/{}/metadata".format(device.mac_id))

    assert r.status_code == HTTP_403_FORBIDDEN
    response_body = r.json()


def test_get_device_metadata_with_invalid_api_key_raises_403(
    client: TestClient, db: Session
):
    agent_user = get_default_agent_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(10), creator_id=agent_user.id, agent_id=agent_user.id
        ),
    )

    device = device_repo.activate_device(db, device_obj=device)

    assert device
    assert device.is_active
    from backend.app.api.routes import device as device_routes

    with mock.patch.object(device_routes, "API_KEY_AUTH_ENABLED", True):
        r = client.get(
            "/api/devices/{}/metadata".format(device.mac_id),
            headers={"X-API-KEY": "Some Invalid API Key"},
        )
        assert r.status_code == HTTP_403_FORBIDDEN


def test_get_metadata_for_non_existent_device_rasies_404(
    client: TestClient, db: Session
):
    r = client.get(
        "/api/devices/{}/metadata".format("some-random-mac-id"),
        headers={"X-API-KEY": "Some Invalid API Key"},
    )
    assert r.status_code == HTTP_404_NOT_FOUND


def test_get_metadata_for_inactive_device_rasies_403(client: TestClient, db: Session):
    agent_user = get_default_agent_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(10), creator_id=agent_user.id, agent_id=agent_user.id
        ),
    )

    assert device
    assert not device.is_active

    r = client.get(
        "/api/devices/{}/metadata".format(device.mac_id),
        headers={"X-API-KEY": "Some Invalid API Key"},
    )

    assert r.status_code == HTTP_403_FORBIDDEN

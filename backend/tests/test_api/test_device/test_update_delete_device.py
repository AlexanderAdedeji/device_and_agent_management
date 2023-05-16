from backend.app.schemas.device import DeviceCreate
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from backend.tests.utils import (
    create_agent_user,
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

import random


def test_update_device_as_device_creator(db: Session, client: TestClient):
    user = get_default_agent_user(db)
    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=user.id, agent_id=user.id
        ),
    )

    assert device

    new_mac_id = random_string(10)
    r = client.put(
        "/api/devices/{}".format(device.id),
        headers=generate_header_from_user_obj(user),
        json={"mac_id": new_mac_id},
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    device = device_repo.get_by_field(db, field_name="mac_id", field_value=new_mac_id)

    assert device
    assert device.id == r.json()["id"]


def test_update_device_with_invalid_id_gives_404_status(
    db: Session, client: TestClient
):
    user = get_default_agent_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=user.id, agent_id=user.id
        ),
    )

    assert device

    new_mac_id = random_string(10)
    r = client.put(
        "/api/devices/1234{}".format(device.id),
        headers=generate_header_from_user_obj(user),
        json={"mac_id": new_mac_id},
    )

    assert r.status_code == HTTP_404_NOT_FOUND

    device = device_repo.get_by_field(db, field_name="mac_id", field_value=new_mac_id)

    assert not device


def test_update_device_as_superuser(db: Session, client: TestClient):
    creator_user = get_default_agent_user(db)

    user = get_default_superuser(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )
    assert device
    new_mac_id = random_string()
    r = client.put(
        "/api/devices/{}".format(device.id),
        headers=generate_header_from_user_obj(user),
        json={"mac_id": new_mac_id},
    )

    resp_body = r.json()

    assert r.status_code == HTTP_200_OK
    device = device_repo.get_by_field(db, field_name="mac_id", field_value=new_mac_id)

    assert device
    assert device.id == resp_body["id"]


def test_update_device_as_non_creator(db: Session, client: TestClient):
    creator_user = get_default_agent_user(db)

    new_agent_user = create_agent_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )

    assert device

    r = client.put(
        "/api/devices/{}".format(device.id),
        headers=generate_header_from_user_obj(new_agent_user),
        json={"mac_id": random_string()},
    )

    resp_body = r.json()

    assert r.status_code == HTTP_403_FORBIDDEN
    assert "errors" in resp_body


def test_delete_device_as_device_creator(db: Session, client: TestClient):
    user = create_agent_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=user.id, agent_id=user.id
        ),
    )
    assert device

    r = client.delete(
        "/api/devices/{}".format(device.id), headers=generate_header_from_user_obj(user)
    )
    resp_body = r.json()

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED
    assert "id" in resp_body
    assert "mac_id" in resp_body

    assert not device_repo.get(db, id=resp_body["id"])


def test_delete_device_with_invalid_id_gives_404_status(
    db: Session, client: TestClient
):
    user = get_default_agent_user(db)

    r = client.delete(
        "/api/devices/123456789",
        headers=generate_header_from_user_obj(user),
    )
    resp_body = r.json()

    assert r.status_code == HTTP_404_NOT_FOUND


def test_delete_device_as_superuser(db: Session, client: TestClient):
    creator_user = get_default_agent_user(db)

    user = get_default_superuser(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )
    assert device

    r = client.delete(
        "/api/devices/{}".format(device.id), headers=generate_header_from_user_obj(user)
    )
    resp_body = r.json()

    assert r.status_code == HTTP_200_OK
    assert "id" in resp_body

    assert not device_repo.get(db, id=resp_body["id"])


def test_delete_device_as_non_creator(db: Session, client: TestClient):
    creator_user = get_default_agent_user(db)

    user = get_agent_employee_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )

    assert device

    r = client.delete(
        "/api/devices/{}".format(device.id), headers=generate_header_from_user_obj(user)
    )

    resp_body = r.json()

    assert r.status_code == HTTP_403_FORBIDDEN
    assert "errors" in resp_body

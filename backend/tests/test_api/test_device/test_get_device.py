from logging import debug
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
from random import randint


def test_get_device_as_device_creator(db: Session, client: TestClient):
    user = get_default_agent_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=user.id, agent_id=user.id
        ),
    )

    assert device

    r = client.get(
        "/api/devices/{}".format(device.id), headers=generate_header_from_user_obj(user)
    )
    resp_body = r.json()

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED
    assert "id" in resp_body
    assert "mac_id" in resp_body


def test_get_device_with_invalid_id_gives_404(db: Session, client: TestClient):
    user = get_default_superuser(db)

    r = client.get(
        "/api/devices/12345",
        headers=generate_header_from_user_obj(user),
    )

    assert r.status_code == HTTP_404_NOT_FOUND


def test_agent_employee_user_can_get_device_hes_assigned_to(
    db: Session, client: TestClient
):
    assigned_user = get_agent_employee_user(db)
    initially_assigned_devices = assigned_user.devices

    creator_user = get_default_agent_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )

    device_repo.add_assigned_user(db, device_obj=device, user_obj=assigned_user)

    assert len(assigned_user.devices) == 1 + len(initially_assigned_devices)
    assert device in assigned_user.devices

    r = client.get(
        "/api/devices/{}".format(device.id),
        headers=generate_header_from_user_obj(assigned_user),
    )

    assert r.status_code == HTTP_200_OK
    assert r.json()["id"] == device.id


def test_get_device_as_superuser(db: Session, client: TestClient):
    creator_user = get_default_agent_user(db)

    user = get_default_superuser(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )
    assert device

    r = client.get(
        "/api/devices/{}".format(device.id), headers=generate_header_from_user_obj(user)
    )
    resp_body = r.json()

    assert r.status_code == HTTP_200_OK
    assert "id" in resp_body


def test_get_device_as_non_creator_and_not_assigned(db: Session, client: TestClient):
    creator_user = get_default_agent_user(db)

    new_agent_user = create_agent_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )
    assert device

    r = client.get(
        "/api/devices/{}".format(device.id),
        headers=generate_header_from_user_obj(new_agent_user),
    )

    resp_body = r.json()

    assert r.status_code == HTTP_403_FORBIDDEN
    assert "errors" in resp_body

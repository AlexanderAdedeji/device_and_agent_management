from backend.app.schemas.device import DeviceCreate
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_403_FORBIDDEN
from backend.tests.utils import (
    create_agent_user,
    generate_header_from_user_obj,
    get_default_agent_employee_user,
    get_default_agent_user,
    get_default_superuser,
    random_string,
)
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.db.repositories.device import device_repo


def test_activate_device_as_superuser(db: Session, client: TestClient):
    user = get_default_superuser(db)
    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=user.id, agent_id=user.id
        ),
    )

    assert device

    r = client.post(
        "/api/devices/activate/{}".format(device.id),
        headers=generate_header_from_user_obj(user),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    device = device_repo.get(db, id=device.id)
    db.refresh(device)

    assert device
    assert device.is_active


def test_activate_device_as_creator_agent_suceeds(db: Session, client: TestClient):
    user = get_default_agent_user(db)
    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=user.id, agent_id=user.id
        ),
    )

    assert device

    r = client.post(
        "/api/devices/activate/{}".format(device.id),
        headers=generate_header_from_user_obj(user),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    device = device_repo.get(db, id=device.id)
    db.refresh(device)

    assert device
    assert device.is_active


def test_activate_device_not_owned_by_agent_fails(db: Session, client: TestClient):
    creator_user = get_default_agent_user(db)
    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )

    assert device
    assert not device.is_active
    assert device.agent_id == creator_user.id

    new_agent_user = create_agent_user(db)

    r = client.post(
        "/api/devices/deactivate/{}".format(device.id),
        headers=generate_header_from_user_obj(new_agent_user),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    device = device_repo.get(db, id=device.id)
    db.refresh(device)
    assert not device.is_active


def test_activate_device_as_agent_employee_fails(db: Session, client: TestClient):
    user = get_default_agent_employee_user(db)
    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=user.id, agent_id=user.id
        ),
    )

    assert device

    r = client.post(
        "/api/devices/activate/{}".format(device.id),
        headers=generate_header_from_user_obj(user),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    device = device_repo.get(db, id=device.id)

    assert device
    assert not device.is_active


def test_deactivate_device_as_superuser(db: Session, client: TestClient):
    creator_user = get_default_agent_user(db)
    user = get_default_superuser(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )
    assert device

    device = device_repo.activate_device(db, device_obj=device)

    r = client.post(
        "/api/devices/deactivate/{}".format(device.id),
        headers=generate_header_from_user_obj(user),
    )

    assert r.status_code == HTTP_200_OK
    device = device_repo.get(db, id=device.id)
    db.refresh(device)

    assert device
    assert not device.is_active


def test_deactivate_device_as_creator_agent_works(db: Session, client: TestClient):
    user = get_default_agent_user(db)
    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=user.id, agent_id=user.id
        ),
    )

    assert device

    device = device_repo.activate_device(db, device_obj=device)

    r = client.post(
        "/api/devices/deactivate/{}".format(device.id),
        headers=generate_header_from_user_obj(user),
    )

    assert r.status_code == HTTP_200_OK

    device = device_repo.get(db, id=device.id)
    db.refresh(device)

    assert device
    assert not device.is_active


def test_deactivate_device_you_dont_own_as_agent_fails(db: Session, client: TestClient):
    creator_user = get_default_agent_user(db)
    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )

    device = device_repo.activate_device(db, device_obj=device)

    assert device
    assert device.is_active
    assert device.agent_id == creator_user.id

    new_agent_user = create_agent_user(db)

    r = client.post(
        "/api/devices/deactivate/{}".format(device.id),
        headers=generate_header_from_user_obj(new_agent_user),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    device = device_repo.get(db, id=device.id)
    db.refresh(device)
    assert device.is_active


def test_deactivate_device_as_agent_employee_fails(db: Session, client: TestClient):
    user = get_default_agent_employee_user(db)
    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=user.id, agent_id=user.id
        ),
    )

    assert device

    device = device_repo.activate_device(db, device_obj=device)

    r = client.post(
        "/api/devices/deactivate/{}".format(device.id),
        headers=generate_header_from_user_obj(user),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    device = device_repo.get(db, id=device.id)
    db.refresh(device)

    assert device
    assert device.is_active

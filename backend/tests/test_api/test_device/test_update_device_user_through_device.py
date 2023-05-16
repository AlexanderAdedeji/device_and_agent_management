from backend.app.schemas.api_key import APIKeyCreate
from backend.app.schemas.device import DeviceCreate
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from tests.utils import (
    create_agent_employee_user,
    get_default_agent_user,
    random_string,
)
from backend.app.db.repositories.api_key import api_key_repository
from backend.app.db.repositories.device import device_repo
from backend.app.services.security import verify_password


def test_update_device_user_without_api_key(db: Session, client: TestClient):
    agent = get_default_agent_user(db)
    user_to_be_assigned = create_agent_employee_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=agent.id, agent_id=agent.id
        ),
    )

    update_body = {"password": "newpassword"}
    res = client.put(
        "api/devices/{}/device_users/{}".format(device.mac_id, user_to_be_assigned.id),
        json=update_body,
    )

    assert res.status_code == HTTP_403_FORBIDDEN


def test_update_device_user_with_api_key(db: Session, client: TestClient):
    agent = get_default_agent_user(db)
    user_to_be_assigned = create_agent_employee_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=agent.id, agent_id=agent.id
        ),
    )
    device_repo.activate_device(db, device_obj=device)

    device_repo.add_assigned_user(db, device_obj=device, user_obj=user_to_be_assigned)

    unsafe_api_key = api_key_repository.create(
        db, api_key_obj=APIKeyCreate(name=random_string(10), user_id=agent.id)
    )
    db.refresh(device)

    assert len(device.assigned_users) == 1
    assert device.agent_id == agent.id
    assert device.assigned_users[0] is user_to_be_assigned

    update_body = {"password": "newpassword"}
    res = client.put(
        "api/devices/{}/device_users/{}".format(device.mac_id, user_to_be_assigned.id),
        json=update_body,
        headers={"X-API-KEY": unsafe_api_key.plain_api_key},
    )

    assert res.status_code == HTTP_200_OK

    db.refresh(user_to_be_assigned)
    assert verify_password("newpassword", user_to_be_assigned.hashed_password)


def test_update_device_user_with_invalid_api_key(db: Session, client: TestClient):
    agent = get_default_agent_user(db)
    user_to_be_assigned = create_agent_employee_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=agent.id, agent_id=agent.id
        ),
    )
    device_repo.activate_device(db, device_obj=device)

    device_repo.add_assigned_user(db, device_obj=device, user_obj=user_to_be_assigned)

    unsafe_api_key = api_key_repository.create(
        db, api_key_obj=APIKeyCreate(name=random_string(10), user_id=agent.id)
    )
    db.refresh(device)

    assert len(device.assigned_users) == 1
    assert device.agent_id == agent.id
    assert device.assigned_users[0] is user_to_be_assigned

    update_body = {"password": "newpassword"}
    res = client.put(
        "api/devices/{}/device_users/{}".format(device.mac_id, user_to_be_assigned.id),
        json=update_body,
        headers={"X-API-KEY": unsafe_api_key.plain_api_key},
    )

    assert res.status_code == HTTP_200_OK

    db.refresh(user_to_be_assigned)
    assert verify_password("newpassword", user_to_be_assigned.hashed_password)


def test_update_device_user_not_assigned_to_device_fails(
    db: Session, client: TestClient
):
    agent = get_default_agent_user(db)
    user_to_be_assigned = create_agent_employee_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=agent.id, agent_id=agent.id
        ),
    )
    device_repo.activate_device(db, device_obj=device)
    db.refresh(device)

    assert len(device.assigned_users) == 0
    assert device.agent_id == agent.id

    update_body = {"password": "newpassword"}

    unsafe_api_key = api_key_repository.create(
        db, api_key_obj=APIKeyCreate(name=random_string(10), user_id=agent.id)
    )
    res = client.put(
        "api/devices/{}/device_users/{}".format(device.mac_id, user_to_be_assigned.id),
        json=update_body,
        headers={"X-API-KEY": unsafe_api_key.plain_api_key},
    )

    assert res.status_code == HTTP_403_FORBIDDEN

    db.refresh(user_to_be_assigned)
    assert not verify_password("newpassword", user_to_be_assigned.hashed_password)


def test_update_device_with_invalid_api_key_raises_403(client: TestClient, db: Session):
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
    from unittest import mock

    with mock.patch.object(device_routes, "API_KEY_AUTH_ENABLED", True):
        r = client.put(
            "/api/devices/{}/device_users/{}".format(device.mac_id, agent_user.id),
            headers={"X-API-KEY": "Some Invalid API Key"},
            json={"password": "newpassword"},
        )
        assert r.status_code == HTTP_403_FORBIDDEN

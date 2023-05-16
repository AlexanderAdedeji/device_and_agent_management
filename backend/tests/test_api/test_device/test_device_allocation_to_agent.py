from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from backend.app.schemas.device import DeviceCreate
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.tests.utils import (
    generate_header_from_user_obj,
    get_default_agent_employee_user,
    get_default_agent_user,
    get_default_superuser,
    random_string,
)

from backend.app.db.repositories.device import device_repo


def test_can_allocate_device_to_agent_with_superuser_user(
    db: Session, client: TestClient
):
    superuseruser = get_default_superuser(db)

    device = device_repo.create(
        db, obj_in=DeviceCreate(mac_id=random_string(), creator_id=superuseruser.id,agent_id=superuseruser.id)
    )
    assert device

    agent_user = get_default_agent_user(db)

    r = client.post(
        "/api/devices/{}/allocate_to_agent/{}".format(device.id, agent_user.id),
        headers=generate_header_from_user_obj(superuseruser),
    )

    assert r.status_code == HTTP_200_OK

    # device = device_repo.get(db, id=device.id)
    db.refresh(device)
    assert device.agent_id == agent_user.id


def test_non_superuser_users_can_not_allocate(db: Session, client: TestClient):
    agent_user = get_default_agent_user(db)
    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=agent_user.id, agent_id=agent_user.id
        ),
    )
    assert device

    r = client.post(
        "/api/devices/{}/allocate_to_agent/{}".format(device.id, agent_user.id),
        headers=generate_header_from_user_obj(agent_user),
    )

    assert r.status_code == HTTP_403_FORBIDDEN


def test_allocating_device_to_non_agent_fails(db: Session, client: TestClient):
    superuser = get_default_superuser(db)
    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=superuser.id, agent_id=superuser.id
        ),
    )
    assert device
    agent_employee_user = get_default_agent_employee_user(db)
    r = client.post(
        "/api/devices/{}/allocate_to_agent/{}".format(
            device.id, agent_employee_user.id
        ),
        headers=generate_header_from_user_obj(superuser),
    )

    assert r.status_code == HTTP_403_FORBIDDEN


def test_allocating_non_existent_device_raises_404(db: Session, client: TestClient):
    superuser = get_default_superuser(db)
    non_existent_device_id = 12345678

    agent_employee_user = get_default_agent_employee_user(db)
    r = client.post(
        "/api/devices/{}/allocate_to_agent/{}".format(
            non_existent_device_id, agent_employee_user.id
        ),
        headers=generate_header_from_user_obj(superuser),
    )

    assert r.status_code == HTTP_404_NOT_FOUND


def test_allocating_device_to_non_existent_user_raises_404(
    db: Session, client: TestClient
):
    superuser = get_default_superuser(db)
    non_existent_user_id = 12345678

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=superuser.id, agent_id=superuser.id
        ),
    )
    assert device

    r = client.post(
        "/api/devices/{}/allocate_to_agent/{}".format(device.id, non_existent_user_id),
        headers=generate_header_from_user_obj(superuser),
    )

    assert r.status_code == HTTP_404_NOT_FOUND
from typing import List

from backend.app.models.device import Device
from backend.app.db.repositories.device import device_repo
from backend.app.db.repositories.user import user_repo
from backend.app.schemas.device import DeviceCreate
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import Session
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
    get_default_agent_employee_user,
    get_default_agent_user,
    get_default_superuser,
    random_string,
)


def test_assign_device_using_agent_succeeds(db: Session, client: TestClient):
    user = get_default_agent_user(db)

    user_to_be_assigned = get_agent_employee_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=user.id, agent_id=user.id
        ),
    )

    device_repo.activate_device(db, device_obj=device)

    assert device
    assert device.is_active
    assert len(device.assigned_users) == 0

    r = client.post(
        "/api/devices/assign/{}/{}".format(device.id, user_to_be_assigned.id),
        headers=generate_header_from_user_obj(user),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    device = device_repo.get(db, id=device.id)
    db.refresh(device)

    assert device.assigned_users
    assert len(device.assigned_users) == 1
    assert device.assigned_users[0] is user_to_be_assigned


def test_assign_device_which_agent_does_not_own_to_a_user_fails(
    db: Session, client: TestClient
):
    creator_user = get_default_agent_user(db)

    another_agent_user = create_agent_user(db)

    user_to_be_assigned = get_agent_employee_user(db)

    user_repo.update(
        db, db_obj=user_to_be_assigned, obj_in={"created_by_id": another_agent_user.id}
    )

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )

    device_repo.activate_device(db, device_obj=device)

    assert device
    assert device.is_active
    assert len(device.assigned_users) == 0

    r = client.post(
        "/api/devices/assign/{}/{}".format(device.id, user_to_be_assigned.id),
        headers=generate_header_from_user_obj(another_agent_user),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    device = device_repo.get(db, id=device.id)
    db.refresh(device)

    assert not device.assigned_users
    assert len(device.assigned_users) == 0


def test_assign_device_to_a_nonexistent_user_fails(db: Session, client: TestClient):
    creator_user = get_default_agent_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )

    device_repo.activate_device(db, device_obj=device)

    assert device
    assert device.is_active
    assert len(device.assigned_users) == 0

    r = client.post(
        "/api/devices/assign/{}/123{}".format(device.id, 123),
        headers=generate_header_from_user_obj(creator_user),
    )

    assert r.status_code == HTTP_404_NOT_FOUND

    device = device_repo.get(db, id=device.id)
    db.refresh(device)

    assert not device.assigned_users
    assert len(device.assigned_users) == 0


def test_assign_device_which_is_inactive_fails(db: Session, client: TestClient):
    creator_user = get_default_agent_user(db)

    user_to_be_assigned = get_agent_employee_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )

    assert device
    assert not device.is_active
    assert len(device.assigned_users) == 0

    r = client.post(
        "/api/devices/assign/{}/{}".format(device.id, user_to_be_assigned.id),
        headers=generate_header_from_user_obj(creator_user),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    device = device_repo.get(db, id=device.id)
    db.refresh(device)

    assert not device.assigned_users
    assert not device.is_active
    assert len(device.assigned_users) == 0


def test_assign_device_as_agent_employee_user_fails(db: Session, client: TestClient):
    superuser = get_default_superuser(db)
    user_to_be_assigned = get_agent_employee_user(db)

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=superuser.id, agent_id=superuser.id
        ),
    )

    assert device

    r = client.post(
        "/api/devices/assign/{}/{}".format(device.id, user_to_be_assigned.id),
        headers=generate_header_from_user_obj(superuser),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    device = device_repo.get(db, id=device.id)

    assert device
    assert len(device.assigned_users) == 0


def test_unassign_device_using_agent_succeeds(db: Session, client: TestClient):
    creator_user = get_default_agent_user(db)

    user_to_be_assigned = get_agent_employee_user(db)

    created_devices = [
        device_repo.create(
            db,
            obj_in=DeviceCreate(
                mac_id=random_string(),
                creator_id=creator_user.id,
                agent_id=creator_user.id,
            ),
        )
        for _ in range(3)
    ]
    for device in created_devices:
        device_repo.add_assigned_user(
            db, device_obj=device, user_obj=user_to_be_assigned
        )

    for device in created_devices:
        assert device
        assert device.id
        assert device.creator_id == creator_user.id
        assert len(device.assigned_users) == 1
        assert device.assigned_users[0] is user_to_be_assigned

    r = client.post(
        "/api/devices/unassign/{}/{}".format(
            created_devices[0].id, user_to_be_assigned.id
        ),
        headers=generate_header_from_user_obj(creator_user),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    device = device_repo.get(db, id=created_devices[0].id)
    db.refresh(device)

    assert len(device.assigned_users) == 0


def test_unassign_device_without_credentials_fails(db: Session, client: TestClient):
    creator_user = get_default_superuser(db)
    user_to_be_assigned = get_agent_employee_user(db)

    created_devices = [
        device_repo.create(
            db,
            obj_in=DeviceCreate(
                mac_id=random_string(),
                creator_id=creator_user.id,
                agent_id=creator_user.id,
            ),
        )
        for _ in range(1)
    ]

    for device in created_devices:
        device_repo.add_assigned_user(
            db, device_obj=device, user_obj=user_to_be_assigned
        )

    for device in created_devices:
        assert device
        assert device.id
        assert device.creator_id == creator_user.id

    for device in created_devices:
        assert len(device.assigned_users) == 1
        assert device.assigned_users[0] is user_to_be_assigned

    r = client.post(
        "/api/devices/unassign/{}/{}".format(
            created_devices[0].id, user_to_be_assigned.id
        )
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    device = device_repo.get(db, id=created_devices[0].id)
    db.refresh(device)

    assert len(device.assigned_users) == 1
    assert device.assigned_users[0] is user_to_be_assigned


def test_get_all_devices_assigned_to_user_with_user_id_with_superuser_account_succeeds(
    db: Session, client: TestClient
):
    user = get_default_superuser(db)

    user_to_be_assigned = get_agent_employee_user(db)
    initially_assigned_devices = user_to_be_assigned.devices

    created_devices: List[Device] = [
        device_repo.create(
            db,
            obj_in=DeviceCreate(
                mac_id=random_string(), creator_id=user.id, agent_id=user.id
            ),
        )
        for _ in range(3)
    ]

    for device in created_devices:
        device_repo.add_assigned_user(
            db, device_obj=device, user_obj=user_to_be_assigned
        )

    for device in created_devices:
        assert len(device.assigned_users) == 1

    r = client.get(
        "/api/devices/assigned/{}".format(user_to_be_assigned.id),
        headers=generate_header_from_user_obj(user),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    resp_body = r.json()

    assert len(resp_body) == 3 + len(initially_assigned_devices)


def test_get_all_devices_assigned_to_user_with_user_id_with_creator_account_succeeds(
    db: Session, client: TestClient
):
    creator_user = get_default_agent_user(db)

    user_to_be_assigned = get_agent_employee_user(db)
    initially_assigned_devices = user_to_be_assigned.devices
    user_repo.update(
        db, db_obj=user_to_be_assigned, obj_in={"created_by_id": creator_user.id}
    )

    created_devices: List[Device] = [
        device_repo.create(
            db,
            obj_in=DeviceCreate(
                mac_id=random_string(),
                creator_id=creator_user.id,
                agent_id=creator_user.id,
            ),
        )
        for _ in range(3)
    ]

    for device in created_devices:
        device_repo.add_assigned_user(
            db, device_obj=device, user_obj=user_to_be_assigned
        )

    for device in created_devices:
        assert len(device.assigned_users) == 1

    r = client.get(
        "/api/devices/assigned/{}".format(user_to_be_assigned.id),
        headers=generate_header_from_user_obj(creator_user),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    resp_body = r.json()

    assert len(resp_body) == 3 + len(initially_assigned_devices)


def test_assign_device_to_non_agent_employee_fails(db: Session, client: TestClient):
    creator_user = get_default_superuser(db)
    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            mac_id=random_string(), creator_id=creator_user.id, agent_id=creator_user.id
        ),
    )
    assert device
    device_repo.activate_device(db, device_obj=device)

    agent_user = get_default_agent_user(db)
    agent_employee_user = get_default_agent_employee_user(db)

    r = client.post(
        "/api/devices/assign/{}/{}".format(device.id, agent_user.id),
        headers=generate_header_from_user_obj(creator_user),
    )
    assert r.status_code == HTTP_403_FORBIDDEN

    r = client.post(
        "/api/devices/assign/{}/{}".format(device.id, agent_employee_user.id),
        headers=generate_header_from_user_obj(creator_user),
    )
    assert r.status_code == HTTP_200_OK


def test_get_all_devices_assigned_to_user_using_the_current_users_credentials_succeeds(
    db: Session, client: TestClient
):
    creator_user = get_default_superuser(db)

    user_to_be_assigned = get_agent_employee_user(db)
    initially_assigned_devices = user_to_be_assigned.devices

    created_devices: List[Device] = [
        device_repo.create(
            db,
            obj_in=DeviceCreate(
                mac_id=random_string(),
                creator_id=creator_user.id,
                agent_id=creator_user.id,
            ),
        )
        for _ in range(3)
    ]

    for device in created_devices:
        device_repo.add_assigned_user(
            db, device_obj=device, user_obj=user_to_be_assigned
        )

    for device in created_devices:
        assert len(device.assigned_users) == 1

    r = client.get(
        "/api/devices/assigned/{}".format(user_to_be_assigned.id),
        headers=generate_header_from_user_obj(user_to_be_assigned),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    resp_body = r.json()

    assert len(resp_body) == 3 + len(initially_assigned_devices)

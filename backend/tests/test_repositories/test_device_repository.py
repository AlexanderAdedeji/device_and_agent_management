from backend.app.models.device import Device
from backend.app.db.errors import DBViolationError
from backend.tests.utils import (
    create_agent_employee_user,
    create_agent_user,
    get_agent_employee_user,
    get_default_agent_employee_user,
    get_default_agent_user,
    get_default_superuser,
    random_string,
)
from sqlalchemy.orm import Session
from backend.app.db.repositories.device import device_repo
from backend.app.db.repositories.user import user_repo
from backend.app.schemas.device import DeviceConfig, DeviceCreate
from typing import List
import pytest

from random import choice


def test_create_device(db: Session):
    user = get_default_agent_user(db)
    intial_user_created_devices = device_repo.get_all_devices_with_agent_id(
        db, agent_id=user.id
    )
    mac_id = random_string(10)

    device_obj = DeviceCreate(mac_id=mac_id, creator_id=user.id, agent_id=user.id)

    new_device = device_repo.create(db, obj_in=device_obj)

    assert new_device

    users_created_devices = device_repo.get_all_devices_with_agent_id(
        db, agent_id=user.id
    )
    assert len(users_created_devices) == 1 + len(intial_user_created_devices)
    assert new_device in users_created_devices


def test_create_device_with_same_mac_id_throws_exception(db: Session):
    user = get_default_agent_user(db)
    initial_user_created_devices = device_repo.get_all_devices_with_agent_id(
        db, agent_id=user.id
    )
    mac_id = random_string(10)

    device_obj = DeviceCreate(mac_id=mac_id, creator_id=user.id, agent_id=user.id)

    new_device = device_repo.create(db, obj_in=device_obj)

    assert new_device
    assert len(new_device.assigned_users) == 0

    users_created_devices = device_repo.get_all_devices_with_agent_id(
        db, agent_id=user.id
    )

    assert len(users_created_devices) == 1 + len(initial_user_created_devices)

    with pytest.raises(DBViolationError):
        new_device = device_repo.create(db, obj_in=device_obj)


def test_add_assigned_users_to_device(db: Session):
    user_1 = create_agent_user(db)

    mac_id = random_string(10)

    device_obj = DeviceCreate(mac_id=mac_id, creator_id=user_1.id, agent_id=user_1.id)

    new_device = device_repo.create(db, obj_in=device_obj)

    assert new_device

    user_2 = create_agent_user(db)

    device = device_repo.add_assigned_users(
        db, device_obj=new_device, user_objs=[user_1, user_2]
    )

    assert device

    assert len(device.assigned_users) == 2

    user_1_created_devices = device_repo.get_all_devices_with_agent_id(
        db, agent_id=user_1.id
    )

    user_2_created_devices = device_repo.get_all_devices_with_agent_id(
        db, agent_id=user_2.id
    )

    assert len(user_1_created_devices) == 1
    assert user_1_created_devices[0] == new_device

    assert len(user_2_created_devices) == 0


def test_add_assigned_user_to_device(db: Session):
    user = get_default_agent_user(db)
    initial_created_devices = device_repo.get_all_devices_with_agent_id(
        db, agent_id=user.id
    )

    mac_id = random_string(10)

    device_obj = DeviceCreate(mac_id=mac_id, creator_id=user.id, agent_id=user.id)

    new_device = device_repo.create(db, obj_in=device_obj)

    assert new_device

    device = device_repo.add_assigned_user(db, device_obj=new_device, user_obj=user)

    assert device

    assert len(device.assigned_users) == 1
    agent_devices = device_repo.get_all_devices_with_agent_id(db, agent_id=user.id)
    assert len(agent_devices) == 1 + len(initial_created_devices)
    assert new_device in agent_devices


def test_add_assigned_user_to_device_twice(db: Session):
    user = get_default_agent_user(db)
    initial_created_devices = device_repo.get_all_devices_with_agent_id(
        db, agent_id=user.id
    )

    mac_id = random_string(10)

    device_obj = DeviceCreate(mac_id=mac_id, creator_id=user.id, agent_id=user.id)

    new_device = device_repo.create(db, obj_in=device_obj)

    assert new_device

    device = device_repo.add_assigned_user(db, device_obj=new_device, user_obj=user)
    device = device_repo.add_assigned_user(db, device_obj=new_device, user_obj=user)

    assert device

    assert len(device.assigned_users) == 1

    agent_devices = device_repo.get_all_devices_with_agent_id(db, agent_id=user.id)

    assert len(agent_devices) == 1 + len(initial_created_devices)
    assert device in agent_devices


def test_remove_assigned_user_from_device(db: Session):
    user = get_default_agent_user(db)

    device_obj = DeviceCreate(
        mac_id=random_string(10), creator_id=user.id, agent_id=user.id
    )
    device = device_repo.create(db, obj_in=device_obj)
    device_repo.add_assigned_users(db, device_obj=device, user_objs=[user])

    device = device_repo.remove_assigned_user(db, device_obj=device, user_obj=user)

    assert user not in device.assigned_users


def test_agent_devices_is_updated_on_device_deletion(db: Session):
    user = get_default_agent_user(db)

    mac_id = random_string(10)

    device_obj = DeviceCreate(mac_id=mac_id, creator_id=user.id, agent_id=user.id)

    new_device = device_repo.create(db, obj_in=device_obj)

    assert new_device
    assert len(new_device.assigned_users) == 0

    agent_devices = device_repo.get_all_devices_with_agent_id(db, agent_id=user.id)

    assert new_device in agent_devices

    deleted_device = device_repo.remove(db, id=new_device.id)
    assert deleted_device

    agent_devices = device_repo.get_all_devices_with_agent_id(db, agent_id=user.id)

    assert new_device not in agent_devices


def test_remove_assigned_user_from_device_twice(db: Session):
    agent_user = get_default_agent_user(db)
    agent_employee_user = get_agent_employee_user(db)

    mac_id = random_string(10)

    device_obj = DeviceCreate(
        mac_id=mac_id, creator_id=agent_user.id, agent_id=agent_user.id
    )

    new_device = device_repo.create(db, obj_in=device_obj)

    assert new_device

    agent_user_created_devices = device_repo.get_all_devices_with_agent_id(
        db, agent_id=agent_user.id
    )

    assert new_device in agent_user_created_devices

    new_device = device_repo.add_assigned_users(
        db, device_obj=new_device, user_objs=[agent_employee_user]
    )

    assert len(new_device.assigned_users) == 1

    device_repo.remove_assigned_user(
        db, device_obj=new_device, user_obj=agent_employee_user
    )

    assert len(new_device.assigned_users) == 0

    new_device = device_repo.remove_assigned_user(
        db, device_obj=new_device, user_obj=agent_employee_user
    )

    assert len(new_device.assigned_users) == 0

    agent_user_created_devices = device_repo.get_all_devices_with_agent_id(
        db, agent_id=agent_user.id
    )

    assert new_device in agent_user_created_devices


def test_device_mac_id_existence_check_works_as_expected(db: Session):
    creator_user = get_default_agent_user(db)

    mac_id = random_string(10)

    device_obj = DeviceCreate(
        mac_id=mac_id, creator_id=creator_user.id, agent_id=creator_user.id
    )

    new_device = device_repo.create(db, obj_in=device_obj)

    assert new_device

    assert device_repo.mac_id_exists(db, mac_id)

    device_repo.remove(db, id=new_device.id)

    assert not device_repo.mac_id_exists(db, mac_id)


def test_get_all_devices_assigned_to_user_with_user_id(db: Session):
    mac_ids = [random_string(10) for _ in range(3)]

    creator_user = get_default_agent_user(db)

    created_devices: List[Device] = []

    for mac_id in mac_ids:
        device = device_repo.create(
            db,
            obj_in=DeviceCreate(
                mac_id=mac_id, creator_id=creator_user.id, agent_id=creator_user.id
            ),
        )
        created_devices.append(device)

    for device in created_devices:
        assert device
        assert device.id
        assert device.mac_id in mac_ids

    user_to_be_assigned = create_agent_employee_user(db)

    for device in created_devices:
        device_repo.add_assigned_users(
            db, device_obj=device, user_objs=[user_to_be_assigned]
        )

    all_devices_assigned_to_user = (
        user_repo.get_all_devices_assigned_to_user_with_user_id(
            db, user_id=user_to_be_assigned.id
        )
    )

    assert all_devices_assigned_to_user
    assert len(all_devices_assigned_to_user) == 3

    for device in created_devices[:2]:
        device_repo.remove_assigned_user(
            db, device_obj=device, user_obj=user_to_be_assigned
        )
    all_devices_assigned_to_user = (
        user_repo.get_all_devices_assigned_to_user_with_user_id(
            db, user_id=user_to_be_assigned.id
        )
    )

    assert all_devices_assigned_to_user
    assert len(all_devices_assigned_to_user) == 1
    assert all_devices_assigned_to_user[0] is created_devices[2]
    assert all_devices_assigned_to_user[0].creator_id == creator_user.id


def test_activate_device(db: Session):
    user = get_default_superuser(db)

    mac_id = random_string(10)
    device = device_repo.create(
        db, obj_in=DeviceCreate(mac_id=mac_id, creator_id=user.id, agent_id=user.id)
    )
    assert device
    assert not device.is_active

    device_repo.activate_device(db, device_obj=device)

    assert device.is_active

    device_repo.activate_device(db, device_obj=device)

    assert device.is_active


def test_deactivate_device(db: Session):
    user = get_default_superuser(db)

    mac_id = random_string(10)
    device = device_repo.create(
        db, obj_in=DeviceCreate(mac_id=mac_id, creator_id=user.id, agent_id=user.id)
    )

    assert device
    assert not device.is_active

    device_repo.activate_device(db, device_obj=device)

    assert device.is_active

    device_repo.deactivate_device(db, device_obj=device)

    assert not device.is_active

    device_repo.deactivate_device(db, device_obj=device)

    assert not device.is_active


def test_get_device_config(db: Session):
    user = get_default_superuser(db)

    mac_id = random_string(10)

    device = device_repo.create(
        db, obj_in=DeviceCreate(mac_id=mac_id, creator_id=user.id, agent_id=user.id)
    )
    user2 = get_default_agent_user(db)
    user3 = get_default_agent_employee_user(db)
    device_repo.add_assigned_users(
        db, device_obj=device, user_objs=[user, user, user2, user3]
    )

    config = device_repo.get_device_config(db, device_obj=device)

    assert config
    assert DeviceConfig(**config)

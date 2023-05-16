from backend.app.schemas.device import DeviceCreate
from backend.tests.utils import (
    generate_header_from_user_obj,
    get_default_agent_employee_user,
    get_default_agent_user,
    create_agent_user,
    get_default_superuser,
    create_agent_employee_user,
    random_string,
)
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)

from backend.app.db.repositories.user import user_repo
from backend.app.db.repositories.device import device_repo


def test_can_not_reassign_without_superuser_credentials(
    client: TestClient, db: Session
):
    agent_employee = get_default_agent_employee_user(db)
    agent = get_default_agent_user(db)

    r = client.post("/api/users/{}/change_agent/{}".format(agent_employee.id, agent.id))

    assert r.status_code == HTTP_403_FORBIDDEN


def test_reassigning_works_with_superuser_credentials(client: TestClient, db: Session):
    agent_employee = create_agent_employee_user(db)
    agent = get_default_agent_user(db)

    r = client.post(
        "/api/users/{}/change_agent/{}".format(agent_employee.id, agent.id),
        headers=generate_header_from_user_obj(get_default_superuser(db)),
    )

    assert r.status_code == HTTP_200_OK

    agent_employee = user_repo.get(db, id=agent_employee.id)
    db.refresh(agent_employee)
    assert agent_employee
    assert agent_employee.agent_id == agent.id


def test_can_not_reassign_agent_employee_to_non_agent_user(
    client: TestClient, db: Session
):
    agent_employee = create_agent_employee_user(db)
    original_agent_employee_agent_id = agent_employee.agent_id
    supposed_agent = get_default_superuser(db)

    r = client.post(
        "/api/users/{}/change_agent/{}".format(agent_employee.id, supposed_agent.id),
        headers=generate_header_from_user_obj(get_default_superuser(db)),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    agent_employee = user_repo.get(db, id=agent_employee.id)
    db.refresh(agent_employee)
    assert agent_employee
    assert agent_employee.agent_id == original_agent_employee_agent_id


def test_can_not_reassign_user_who_is_not_agent_employee(
    client: TestClient, db: Session
):
    user_to_reassign = get_default_superuser(db)
    agent = get_default_agent_user(db)

    original_user_to_reassign_agent_id = user_to_reassign.agent_id

    r = client.post(
        "/api/users/{}/change_agent/{}".format(user_to_reassign.id, agent.id),
        headers=generate_header_from_user_obj(get_default_superuser(db)),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    user_to_reassign = user_repo.get(db, id=user_to_reassign.id)
    db.refresh(user_to_reassign)
    assert user_to_reassign
    assert user_to_reassign.agent_id == original_user_to_reassign_agent_id


def test_can_not_assign_agent_employee_to_self(client: TestClient, db: Session):
    agent_employee = create_agent_employee_user(db)
    original_agent_employee_agent_id = agent_employee.agent_id
    user_to_reassign = agent_employee

    r = client.post(
        "/api/users/{}/change_agent/{}".format(user_to_reassign.id, agent_employee.id),
        headers=generate_header_from_user_obj(get_default_superuser(db)),
    )

    assert r.status_code == HTTP_400_BAD_REQUEST
    assert "errors" in r.json()

    agent_employee = user_repo.get(db, id=agent_employee.id)
    db.refresh(agent_employee)
    assert agent_employee
    assert agent_employee.agent_id == original_agent_employee_agent_id


def test_reassignment_of_agent_removes_all_the_devices_previosly_assigned_to_device_user(
    client: TestClient, db: Session
):
    agent_employee = create_agent_employee_user(db)
    agent = get_default_agent_user(db)
    agent_employee.agent_id = agent.id

    agent_employee = user_repo.update(db, db_obj=agent_employee, obj_in={})
    db.refresh(agent_employee)

    assert agent_employee
    assert agent_employee.agent_id == agent.id

    device = device_repo.create(
        db, obj_in=DeviceCreate(mac_id=random_string(), creator_id=agent.id,agent_id=agent.id)
    )
    device_repo.add_assigned_user(db, device_obj=device, user_obj=agent_employee)

    agent_employee = user_repo.get(db, id=agent_employee.id)
    assert len(agent_employee.devices) == 1

    new_agent = create_agent_user(db)

    r = client.post(
        "/api/users/{}/change_agent/{}".format(agent_employee.id, new_agent.id),
        headers=generate_header_from_user_obj(get_default_superuser(db)),
    )

    agent_employee = user_repo.get(db, id=agent_employee.id)
    db.refresh(agent_employee)
    assert agent_employee
    assert agent_employee.agent_id == new_agent.id
    assert len(agent_employee.devices) == 0

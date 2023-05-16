# 1. Test returns all devices
# 2. Test returns all employees
# 3. you can not access except it's yours or youre superuser [Done]
# 4. test agent employee can't access [Done]

from app.schemas.device import DeviceCreate
from app.schemas.user import AgentProfile
from backend.tests.utils import (
    create_agent_employee_user,
    create_agent_user,
    generate_header_from_user_obj,
    generate_user_payload,
    get_agent_employee_user,
    get_default_agent_user,
    get_default_superuser,
    random_string,
)

from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.repositories.device import device_repo
from backend.app.db.repositories.user import user_repo


def test_agent_employee_can_not_access_agent_profile(client: TestClient, db: Session):
    agent = get_default_agent_user(db)
    agent_employee = get_agent_employee_user(db)

    assert agent
    assert agent_employee

    r = client.get(
        f"/api/users/agent_profile/{agent.id}",
        headers=generate_header_from_user_obj(agent_employee),
    )
    assert r.status_code == HTTP_403_FORBIDDEN


def test_agent_profile_contains_all_assigned_devices(client: TestClient, db: Session):
    agent = create_agent_user(db)
    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            agent_id=agent.id, mac_id=random_string(), creator_id=agent.id
        ),
    )
    assert device

    device = device_repo.create(
        db,
        obj_in=DeviceCreate(
            agent_id=agent.id, mac_id=random_string(), creator_id=agent.id
        ),
    )

    assert device

    r = client.get(
        f"/api/users/agent_profile/{agent.id}",
        headers=generate_header_from_user_obj(agent),
    )
    assert r.status_code == HTTP_200_OK

    profile = AgentProfile(**r.json())
    assert profile.agent.id == agent.id
    assert profile.agent.email == agent.email
    assert len(profile.devices) == 2
    assert len(profile.employees) == 0


def test_agent_profile_contains_all_assigned_users(client: TestClient, db: Session):
    agent = create_agent_user(db)
    data = generate_user_payload()

    r = client.post(
        "/api/users/create_agent_employee_user",
        json={**data, "agent_id": agent.id},
        headers=generate_header_from_user_obj(agent),
    )

    agent_employee = user_repo.get(db, id=r.json()["id"])
    assert agent_employee

    assert r.status_code == HTTP_200_OK

    r = client.get(
        f"/api/users/agent_profile/{agent.id}",
        headers=generate_header_from_user_obj(agent),
    )
    assert r.status_code == HTTP_200_OK

    profile = AgentProfile(**r.json())
    assert profile.agent.id == agent.id
    assert len(profile.employees) == 1
    assert len(profile.devices) == 0

    employee = profile.employees[0]
    assert employee.agent_id == agent.id
    assert employee.id == agent_employee.id


def test_agent_can_not_access_profile_that_is_not_his(client: TestClient, db: Session):
    agent = get_default_agent_user(db)
    new_agent = create_agent_user(db)
    r = client.get(
        f"/api/users/agent_profile/{new_agent.id}",
        headers=generate_header_from_user_obj(agent),
    )
    assert r.status_code == HTTP_403_FORBIDDEN

    r = client.get(
        f"/api/users/agent_profile/{agent.id}",
        headers=generate_header_from_user_obj(agent),
    )
    assert r.status_code == HTTP_200_OK


def test_superuser_can_access_any_profile(client: TestClient, db: Session):
    agent = get_default_agent_user(db)
    new_agent = create_agent_user(db)
    superuser = get_default_superuser(db)

    r = client.get(
        f"/api/users/agent_profile/{new_agent.id}",
        headers=generate_header_from_user_obj(superuser),
    )
    assert r.status_code == HTTP_200_OK

    r = client.get(
        f"/api/users/agent_profile/{agent.id}",
        headers=generate_header_from_user_obj(superuser),
    )
    assert r.status_code == HTTP_200_OK

from backend.tests.utils import create_agent_employee_user, create_agent_user
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.status import HTTP_403_FORBIDDEN

from backend.app.db.repositories.user import user_repo


def test_get_all_current_user_employees_gives_403_without_auth_token(
    client: TestClient, db: Session
):
    r = client.get("/api/users/get_all_current_user_employees")

    assert r.status_code == HTTP_403_FORBIDDEN


def test_get_all_current_user_employees_for_agent(client: TestClient, db: Session):
    agent_employee = create_agent_employee_user(db)
    agent = create_agent_user(db)

    agent_employee.agent_id = agent.id

    user_repo.update(db, db_obj=agent_employee, obj_in={})
    db.refresh(agent_employee)

    agent_employees = user_repo.get_all_users_with_agent_id(db, agent_id=agent.id)
    assert len(agent_employees) == 1
    assert agent_employees[0] is agent_employee

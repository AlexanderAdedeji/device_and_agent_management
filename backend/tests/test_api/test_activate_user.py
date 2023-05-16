from backend.app.db.repositories.user import user_repo
from backend.app.models import User
from backend.tests.utils import (
    create_agent_employee_user,
    create_agent_user,
    generate_header_from_user_obj,
    get_default_agent_user,
    get_default_superuser,
)

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

"""
TOOO
1. Test 
2. Functionality
3. Change docs
4. Commit, Deploy


"""


def test_activation_of_created_user_with_superuser_credentials(
    client: TestClient, db: Session
) -> None:
    new_user = create_agent_user(db)
    user_repo.deactivate(db, db_obj=new_user)

    r = client.get(
        "/api/users/activate/" + str(new_user.id),
        headers=generate_header_from_user_obj(get_default_superuser(db)),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    user = user_repo.get(db, id=new_user.id)
    db.refresh(user)
    assert user.is_active


def test_activation_of_user_with_agent_who_does_not_own_the_user_fails(
    client: TestClient, db: Session
):
    new_employee_user = create_agent_employee_user(db)
    new_employee_user = user_repo.deactivate(db, db_obj=new_employee_user)
    assert not new_employee_user.is_active

    r = client.get(
        "/api/users/activate/" + str(new_employee_user.id),
        headers=generate_header_from_user_obj(get_default_agent_user(db)),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    new_employee_user = user_repo.get(db, id=new_employee_user.id)
    assert not new_employee_user.is_active


def test_activation_of_user_with_agent_who_owns_the_user_succeeds(
    client: TestClient, db: Session
):

    new_employee_user = create_agent_employee_user(db)
    new_employee_user = user_repo.deactivate(db, db_obj=new_employee_user)
    assert not new_employee_user.is_active

    agent_user = get_default_agent_user(db)

    new_employee_user = user_repo.update(
        db, db_obj=new_employee_user, obj_in={"agent_id": agent_user.id}
    )
    assert new_employee_user.agent is agent_user

    r = client.get(
        "/api/users/activate/" + str(new_employee_user.id),
        headers=generate_header_from_user_obj(agent_user),
    )

    assert r.status_code == HTTP_200_OK

    new_employee_user = user_repo.get(db, id=new_employee_user.id)
    db.refresh(new_employee_user)
    assert new_employee_user.is_active


def test_deactivation_of_user_with_agent_who_does_not_own_the_user_fails(
    client: TestClient, db: Session
):
    new_employee_user = create_agent_employee_user(db)
    assert new_employee_user.is_active

    r = client.get(
        "/api/users/deactivate/" + str(new_employee_user.id),
        headers=generate_header_from_user_obj(get_default_agent_user(db)),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    new_employee_user = user_repo.get(db, id=new_employee_user.id)
    assert new_employee_user.is_active


def test_deactivation_of_user_with_agent_who_owns_the_user_succeeds(
    client: TestClient, db: Session
):

    new_employee_user = create_agent_employee_user(db)
    assert new_employee_user.is_active

    agent_user = get_default_agent_user(db)

    new_employee_user = user_repo.update(
        db, db_obj=new_employee_user, obj_in={"agent_id": agent_user.id}
    )

    assert new_employee_user.agent is agent_user

    r = client.get(
        "/api/users/deactivate/" + str(new_employee_user.id),
        headers=generate_header_from_user_obj(agent_user),
    )

    assert r.status_code == HTTP_200_OK

    new_employee_user = user_repo.get(db, id=new_employee_user.id)
    db.refresh(new_employee_user)
    assert not new_employee_user.is_active


def test_deactivation_of_created_user_with_superuser_credentials(
    client: TestClient, db: Session
) -> None:
    new_user = create_agent_user(db)
    original_active_status = new_user.is_active

    r = client.get(
        "/api/users/deactivate/" + str(new_user.id),
        headers=generate_header_from_user_obj(get_default_superuser(db)),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    user = user_repo.get(db, id=new_user.id)
    db.refresh(user)
    assert not user.is_active


def test_activation_of_created_user_without_credentials(
    client: TestClient, db: Session
) -> None:

    agent_user = get_default_agent_user(db)
    original_active_status = agent_user.is_active
    r = client.get(
        "/api/users/activate/" + str(agent_user.id),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    user = user_repo.get(db, id=agent_user.id)
    db.refresh(user)
    assert user.is_active is original_active_status


def test_activation_of_nonexistent_user(client: TestClient, db: Session) -> None:
    RANDOM_ID = 1 << 25
    r = client.get(
        "/api/users/activate/" + str(RANDOM_ID),
        headers=generate_header_from_user_obj(get_default_superuser(db)),
    )

    assert r.status_code == HTTP_404_NOT_FOUND

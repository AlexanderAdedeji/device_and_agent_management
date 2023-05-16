from typing import Dict, Any

from backend.app.core.settings import settings

from backend.app.db.repositories.user import user_repo
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from backend.tests.utils import (
    create_superuser_user,
    generate_header_from_user_obj,
    get_default_agent_user,
    create_agent_employee_user,
    get_default_superuser,
    get_superuser_auth_header,
)

REGULAR_USER_TYPE = settings.REGULAR_USER_TYPE


def test_making_of_created_user_a_superuser_with_superuser_account(
    client: TestClient, db: Session
) -> None:
    new_user = create_agent_employee_user(db)
    assert not new_user.is_superuser

    r = client.get(
        "/api/users/grant_superuser_status/" + str(new_user.id),
        headers=generate_header_from_user_obj(get_default_superuser(db)),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    user = user_repo.get(db, id=new_user.id)

    db.refresh(user)

    assert user.is_superuser


def test_granting_superuser_of_created_user_without_superuser_account(
    client: TestClient, db: Session
) -> None:

    user = get_default_agent_user(db)

    r = client.get(
        "/api/users/grant_superuser_status/" + str(user.id),
        headers=generate_header_from_user_obj(user),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    user = user_repo.get(db, id=user.id)
    db.refresh(user)
    assert not user.is_superuser


def test_granting_superuser_status_of_created_user_without_credentials(
    client: TestClient, db: Session
) -> None:

    existing_user = get_default_agent_user(db)
    initial_superuser_status = existing_user.is_superuser
    r = client.get(
        "/api/users/grant_superuser_status/" + str(existing_user.id),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    existing_user = user_repo.get(db, id=existing_user.id)
    db.refresh(existing_user)
    assert existing_user.is_superuser == initial_superuser_status


def test_grant_superuser_status_of_nonexistent_user(
    client: TestClient, db: Session
) -> None:
    RANDOM_ID = 1 << 25
    r = client.get(
        "/api/users/grant_superuser_status/" + str(RANDOM_ID),
        headers=get_superuser_auth_header(db),
    )

    assert r.status_code == HTTP_404_NOT_FOUND


def test_remove_superuser_status_of_non_superuser(client: TestClient, db: Session):
    agent_employee_user = create_agent_employee_user(db)
    r = client.get(
        "/api/users/remove_superuser_status/" + str(agent_employee_user.id),
        headers=get_superuser_auth_header(db),
    )
    assert r.status_code == HTTP_400_BAD_REQUEST


def test_remove_superuser_status_of_nonexistent_user(
    client: TestClient, db: Session
) -> None:
    RANDOM_ID = 1 << 25
    r = client.get(
        "/api/users/remove_superuser_status/" + str(RANDOM_ID),
        headers=get_superuser_auth_header(db),
    )

    assert r.status_code == HTTP_404_NOT_FOUND


def test_remove_superuser_status_assigns_regular_usertype_to_user(
    client: TestClient, db: Session
) -> None:
    new_user = create_superuser_user(db)
    assert new_user.is_superuser

    r = client.get(
        "/api/users/remove_superuser_status/" + str(new_user.id),
        headers=generate_header_from_user_obj(get_default_superuser(db)),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    user = user_repo.get(db, id=new_user.id)

    db.refresh(user)

    assert not user.is_superuser
    assert user.user_type.name == REGULAR_USER_TYPE


def test_revoking_superuser_status_of_created_user_without_superusercredentials(
    client: TestClient, db: Session
) -> None:

    existing_super_user = get_default_superuser(db)
    initial_superuser_status = existing_super_user.is_superuser
    r = client.get(
        "/api/users/remove_superuser_status/" + str(existing_super_user.id),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    existing_user = user_repo.get(db, id=existing_super_user.id)
    db.refresh(existing_user)
    assert existing_user.is_superuser == initial_superuser_status

from backend.app.services.jwt import get_id_from_token
from fastapi.testclient import TestClient
from starlette.status import (
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
    HTTP_201_CREATED,
)
from backend.app.schemas.user import UserUpdate

from backend.tests.utils import (
    create_agent_user,
    generate_header_from_user_obj,
    get_default_agent_user,
    random_lasrra_id,
    random_email,
)

from backend.app.db.repositories.user import user_repo
from sqlalchemy.orm import Session
from backend.app.services.security import verify_password


def test_updating_of_user_on_multiple_fields(client: TestClient, db: Session) -> None:
    user = create_agent_user(db)

    new_email = random_email()

    r = client.put(
        "/api/users/",
        json={
            "first_name": "New first_name",
            "last_name": "New last_name",
            "password": "newpassword",
            "email": new_email,
        },
        headers=generate_header_from_user_obj(user),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED
    user = user_repo.get_by_email(db, email=new_email)
    db.refresh(user)

    assert user
    assert verify_password("newpassword", user.hashed_password)
    assert user.last_name == "New last_name"
    assert user.first_name == "New first_name"


def test_updating_of_user_without_authentication(
    client: TestClient, db: Session
) -> None:
    r = client.put(
        "/api/users/",
        json={"first_name": "New first_name"},
    )

    assert r.status_code == HTTP_403_FORBIDDEN


def test_updating_of_users_id_fails(client: TestClient, db: Session) -> None:
    user = get_default_agent_user(db)
    original_user_id = user.id
    r = client.put(
        "/api/users/",
        json={"id": 1234},
        headers=generate_header_from_user_obj(user),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    user = user_repo.get_by_email(db, email=user.email)

    assert user
    assert user.id == original_user_id


def test_updating_of_user_email_doesnt_invalidate_token(
    client: TestClient, db: Session
):
    user = create_agent_user(db)
    new_user_email = random_email()
    r = client.put(
        "/api/users/",
        json={"email": new_user_email},
        headers=generate_header_from_user_obj(user),
    )

    assert r.status_code == HTTP_200_OK

    user = user_repo.get(db, user.id)
    db.refresh(user)
    assert user.email == new_user_email
    assert get_id_from_token(user.generate_jwt()) == user.id


def test_updating_of_users_lasrra_id_fails(client: TestClient, db: Session) -> None:

    user = get_default_agent_user(db)
    original_lassra_id = user.lasrra_id

    r = client.put(
        "/api/users/",
        json={"lasrra_id": random_lasrra_id()},
        headers=generate_header_from_user_obj(user),
    )

    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    user = user_repo.get_by_email(db, email=user.email)
    db.refresh(user)
    assert user.lasrra_id == original_lassra_id

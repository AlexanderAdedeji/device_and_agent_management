from backend.app.schemas.api_key import APIKeyCreate, APIKeyInResponse
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from backend.app.db.repositories.api_key import api_key_repository
from tests.utils import (
    create_agent_user,
    generate_header_from_user_obj,
    get_default_agent_employee_user,
    get_default_superuser,
    random_string,
)


def test_create_api_key(db: Session, client: TestClient):
    user = create_agent_user(db)

    r = client.post(
        "api/api_keys/",
        headers=generate_header_from_user_obj(user),
        json={"name": random_string(10)},
    )

    assert r.status_code == HTTP_200_OK

    r = client.get(
        "api/api_keys/",
        headers=generate_header_from_user_obj(user),
    )

    assert r.status_code == HTTP_200_OK

    body = r.json()
    assert len(body) == 1


def test_get_all_owned_api_keys(db: Session, client: TestClient):
    user = create_agent_user(db)

    api_key = api_key_repository.create(
        db, api_key_obj=APIKeyCreate(user_id=user.id, name=random_string(10))
    )

    r = client.get(
        "api/api_keys/",
        headers=generate_header_from_user_obj(user),
    )

    assert r.status_code == HTTP_200_OK

    body = r.json()
    assert len(body) == 1

    assert body[0]["id"] == api_key.id


def test_deactivate_api_key(db: Session, client: TestClient):
    user = create_agent_user(db)

    r = client.post(
        "api/api_keys/",
        headers=generate_header_from_user_obj(user),
        json={"name": random_string(10)},
    )

    r = client.delete(
        "api/api_keys/{}".format(r.json()["id"]),
        headers=generate_header_from_user_obj(user),
    )

    assert r.status_code == HTTP_200_OK

    res_body = r.json()

    api_key = APIKeyInResponse(**res_body)

    api_key = api_key_repository.get(db, id=api_key.id)
    assert not api_key.is_active


def test_deactivate_api_key_without_being_the_owner(db: Session, client: TestClient):
    user = create_agent_user(db)

    r = client.post(
        "api/api_keys/",
        headers=generate_header_from_user_obj(user),
        json={"name": random_string(10)},
    )

    r = client.delete(
        "api/api_keys/{}".format(r.json()["id"]),
        headers=generate_header_from_user_obj(get_default_superuser(db)),
    )

    assert r.status_code == HTTP_403_FORBIDDEN


def test_get_all_api_keys_in_system_without_being_superuser_gives_403(
    db: Session, client: TestClient
):
    agent_employee_user = get_default_agent_employee_user(db)

    r = client.get(
        "api/api_keys/all",
        headers=generate_header_from_user_obj(agent_employee_user),
    )
    assert r.status_code == HTTP_403_FORBIDDEN


def test_get_all_api_keys_in_system_with_superuser_account_succeeds(
    db: Session, client: TestClient
):
    superuser = get_default_superuser(db)

    r = client.get("api/api_keys/all", headers=generate_header_from_user_obj(superuser))

    assert r.status_code == HTTP_200_OK

    response_body = r.json()

    all_api_keys = api_key_repository.get_all(db)

    assert len(all_api_keys) == len(response_body)
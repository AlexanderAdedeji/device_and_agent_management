from backend.app.api.dependencies.authentication import AGENT
from backend.app.api.routes.user_types import SUPERUSER_USER_TYPE, AGENT
from backend.app.db.repositories.user import USER_TYPES
from backend.app.schemas.user_type import UserTypeCreate
from backend.app.db.repositories.user_type import user_type as user_type_repo
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)
from backend.tests.utils import (
    create_user_with_type,
    generate_header_from_user_obj,
    get_agent_employee_user,
    random_string,
    get_superuser_auth_header,
)


def test_creating_of_usertype_with_superuser_credentials_works(
    client: TestClient, db: Session
) -> None:
    name = random_string()
    data = {
        "name": name,
    }

    r = client.post(
        "/api/user_types/", json=data, headers=get_superuser_auth_header(db)
    )
    assert HTTP_200_OK <= r.status_code <= HTTP_201_CREATED

    user_type = user_type_repo.get_by_name(db, name=name)
    assert user_type
    assert user_type.name == name


def test_creating_of_usertype_without_credentials_fails(
    client: TestClient, db: Session
) -> None:
    name = random_string()
    data = {
        "name": name,
    }
    r = client.post("/api/user_types/", json=data)
    assert r.status_code == HTTP_403_FORBIDDEN

    user_type = user_type_repo.get_by_name(db, name=name)
    assert user_type is None


def test_creating_of_usertype_with_badpayload_fails(
    client: TestClient, db: Session
) -> None:
    name = random_string()
    data = {}

    r = client.post(
        "/api/user_types/", json=data, headers=get_superuser_auth_header(db)
    )
    assert r.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_deleting_of_usertype_with_superuser_works(
    client: TestClient, db: Session
) -> None:
    name = random_string()
    r = client.post(
        "/api/user_types/", json={"name": name}, headers=get_superuser_auth_header(db)
    )
    assert r.status_code == HTTP_200_OK

    user_type = user_type_repo.get_by_name(db, name=name)
    assert user_type
    assert user_type.name == name

    r = client.delete(
        "/api/user_types/" + str(user_type.id),
        headers=get_superuser_auth_header(db),
    )
    assert r.status_code == HTTP_200_OK

    user_type = user_type_repo.get_by_name(db, name=name)
    assert user_type is None


def test_deleting_of_user_type_which_has_reference_to_users(
    client: TestClient, db: Session
):
    name = random_string()
    r = client.post(
        "/api/user_types/", json={"name": name}, headers=get_superuser_auth_header(db)
    )
    assert r.status_code == HTTP_200_OK

    user_type = user_type_repo.get_by_name(db, name=name)
    assert user_type
    assert user_type.name == name

    new_user = create_user_with_type(db, type_=name)
    assert new_user

    r = client.delete(
        "/api/user_types/" + str(user_type.id),
        headers=get_superuser_auth_header(db),
    )
    assert r.status_code == HTTP_400_BAD_REQUEST

    user_type = user_type_repo.get_by_name(db, name=name)
    assert user_type


def test_updating_of_usertype_with_agent_employee_fails(
    client: TestClient, db: Session
) -> None:
    name = random_string()
    data = {"name": name}

    r = client.post(
        "/api/user_types/", json=data, headers=get_superuser_auth_header(db)
    )

    assert r.status_code == HTTP_200_OK

    user_type = user_type_repo.get_by_name(db, name=name)

    assert user_type

    new_name = random_string()

    data = {"name": new_name}
    r = client.put(
        "/api/user_types/" + str(user_type.id),
        json=data,
        headers=generate_header_from_user_obj(get_agent_employee_user(db)),
    )

    assert r.status_code == HTTP_403_FORBIDDEN

    new_user_type = user_type_repo.get_by_name(db, name=new_name)
    assert new_user_type is None


def test_updating_of_usertype_with_superuser_succeeds(db: Session, client: TestClient):
    name = random_string()
    data = {"name": name}

    r = client.post(
        "/api/user_types/", json=data, headers=get_superuser_auth_header(db)
    )
    assert r.status_code == HTTP_200_OK

    user_type = user_type_repo.get_by_name(db, name=name)

    assert user_type

    new_name = random_string()

    data = {"name": new_name}
    r = client.put(
        "/api/user_types/" + str(user_type.id),
        json=data,
        headers=get_superuser_auth_header(db),
    )

    assert r.status_code == HTTP_200_OK

    new_user_type = user_type_repo.get_by_name(db, name=new_name)
    db.refresh(new_user_type)
    assert new_user_type
    assert new_user_type.name == new_name


def test_updating_of_non_existent_usertype_with_superuser_fails(
    db: Session, client: TestClient
):

    new_name = random_string()

    data = {"name": new_name}
    r = client.put(
        "/api/user_types/" + "1234",
        json=data,
        headers=get_superuser_auth_header(db),
    )

    assert r.status_code == HTTP_404_NOT_FOUND


def test_creating_user_type_with_existing_name_returns_right_error_message(
    db: Session, client: TestClient
):

    r = client.post(
        "/api/user_types/",
        json={"name": SUPERUSER_USER_TYPE},
        headers=get_superuser_auth_header(db),
    )

    assert r.status_code == HTTP_400_BAD_REQUEST
    body = r.json()

    assert "errors" in body
    assert "already exists" in body["errors"][0]["message"]


def test_update_default_user_type_fails(db: Session, client: TestClient):
    superuser_user_type = user_type_repo.get_by_name(db, name=SUPERUSER_USER_TYPE)
    assert superuser_user_type

    r = client.put(
        "/api/user_types/" + str(superuser_user_type.id),
        json={"name": "Some new name"},
        headers=get_superuser_auth_header(db),
    )

    assert r.status_code == HTTP_400_BAD_REQUEST
    body = r.json()

    assert "errors" in body
    assert (
        f"you can not update user type {SUPERUSER_USER_TYPE} as it is a default user type"
        in body["errors"][0]["message"]
    )

    superuser_user_type = user_type_repo.get_by_name(db, name=SUPERUSER_USER_TYPE)
    assert superuser_user_type


def test_delete_default_user_type_fails(db: Session, client: TestClient):
    AGENT = user_type_repo.get_by_name(db, name=AGENT)
    assert AGENT

    r = client.delete(
        "/api/user_types/" + str(AGENT.id),
        headers=get_superuser_auth_header(db),
    )

    assert r.status_code == HTTP_400_BAD_REQUEST
    body = r.json()

    assert "errors" in body
    assert (
        f"you can not delete user type {AGENT} as it is a default user type"
        in body["errors"][0]["message"]
    )

    AGENT = user_type_repo.get_by_name(db, name=AGENT)
    assert AGENT


def test_update_user_type_to_existing_name_returns_right_error_message(
    db: Session, client: TestClient
):
    user_type_name = random_string()
    new_user_type = user_type_repo.create(
        db, obj_in=UserTypeCreate(name=user_type_name)
    )

    r = client.put(
        "/api/user_types/" + str(new_user_type.id),
        json={"name": SUPERUSER_USER_TYPE},
        headers=get_superuser_auth_header(db),
    )

    assert r.status_code == HTTP_400_BAD_REQUEST
    body = r.json()

    assert "errors" in body
    assert "already exists" in body["errors"][0]["message"]


def test_get_all_users_of_usertype_is_not_accesible_by_non_superuser(
    db: Session, client: TestClient
):
    superuser_user_type = user_type_repo.get_by_name(db, name=SUPERUSER_USER_TYPE)

    res = client.get(
        f"/api/user_types/{superuser_user_type.id}/all_users",
        headers=generate_header_from_user_obj(get_agent_employee_user(db)),
    )

    assert res.status_code == HTTP_403_FORBIDDEN


def test_get_all_users_of_usertype_is_accesible_by_superuser(
    db: Session, client: TestClient
):
    new_user_type = user_type_repo.create(
        db, obj_in=UserTypeCreate(name=random_string(10))
    )
    assert new_user_type

    new_user = create_user_with_type(db, type_=new_user_type.name)
    assert new_user

    res = client.get(
        f"/api/user_types/{new_user_type.id}/all_users",
        headers=get_superuser_auth_header(db),
    )
    assert res.status_code == HTTP_200_OK

    response_body = res.json()
    assert len(response_body) == 1
    assert response_body[0]["id"] == new_user.id
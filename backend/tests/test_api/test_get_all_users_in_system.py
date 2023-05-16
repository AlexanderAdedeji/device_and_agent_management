import pytest
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from backend.tests.utils import (
    generate_header_from_user_obj,
    get_default_agent_user,
    get_default_superuser,
)
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.repositories.user import user_repo


def test_get_all_users_in_system_without_superadmin_creds(
    client: TestClient, db: Session
):
    r = client.get(
        "/api/users/all/",
        headers=generate_header_from_user_obj(get_default_agent_user(db)),
    )

    assert r.status_code == HTTP_403_FORBIDDEN


def test_get_all_users_in_system_as_superadmin(client: TestClient, db: Session):

    r = client.get(
        "/api/users/all/",
        headers=generate_header_from_user_obj(get_default_superuser(db)),
    )

    assert r.status_code == HTTP_200_OK

    assert len(user_repo.get_all(db)) == len(r.json())


def test_get_all_users_does_not_contain_users_passwords(
    client: TestClient, db: Session
):
    r = client.get(
        "/api/users/all",
        headers=generate_header_from_user_obj(get_default_superuser(db)),
    )

    assert r.status_code == HTTP_200_OK

    assert len(r.json()) > 0

    user = r.json()[0]
    with pytest.raises(KeyError):
        assert user["password"]
import pytest
from backend.app.db.repositories.user_type import user_type as user_type_repo
from backend.app.schemas.user_type import UserTypeCreate
from sqlalchemy.orm import Session
from backend.tests.utils import random_string


def test_create_user_type(db: Session) -> None:
    type_name = random_string()
    user_type_in = UserTypeCreate(name=type_name)
    user_type_1 = user_type_repo.create(db, obj_in=user_type_in)

    user_type_2 = user_type_repo.get(db, id=user_type_1.id)

    assert user_type_1 is user_type_2


def test_get_user_type_by_name(db: Session) -> None:
    name = random_string()
    user_type_in = UserTypeCreate(name=name)
    user_type_1 = user_type_repo.create(db, obj_in=user_type_in)

    user_type_2 = user_type_repo.get_by_name(db, name=name)
    assert user_type_1 is user_type_2


def test_ensure_unique_name_constraint_is_enforced(db: Session) -> None:
    name = random_string()
    user_type_in = UserTypeCreate(name=name)
    user_type_1 = user_type_repo.create(db, obj_in=user_type_in)
    with pytest.raises(Exception):
        user_type_repo.create(db, obj_in=user_type_in)

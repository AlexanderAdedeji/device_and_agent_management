from sqlalchemy.ext.declarative import api
from sqlalchemy.orm import Session
from tests.utils import create_agent_user, get_default_agent_user
from backend.app.schemas.api_key import APIKeyCreate
from backend.app.db.repositories.api_key import api_key_repository

from backend.tests.utils import random_string


def test_create_api_key(db: Session):
    user = get_default_agent_user(db)

    api_key = api_key_repository.create(
        db, api_key_obj=APIKeyCreate(name=random_string(10), user_id=user.id)
    )

    assert api_key
    assert api_key.user_id is user.id

    assert api_key_repository.get(db, id=api_key.id).user is user


def test_mark_api_key_as_inactive(db: Session):
    user = get_default_agent_user(db)
    unsafe_api_key = api_key_repository.create(
        db, api_key_obj=APIKeyCreate(name=random_string(10), user_id=user.id)
    )
    api_key = api_key_repository.get(db, id=unsafe_api_key.id)
    assert api_key
    assert api_key.is_active

    api_key = api_key_repository.mark_as_inactive(db, api_key_obj=api_key)
    assert not api_key.is_active


def test_mark_api_key_as_active(db: Session):
    user = get_default_agent_user(db)
    unsafe_api_key = api_key_repository.create(
        db, api_key_obj=APIKeyCreate(name=random_string(10), user_id=user.id)
    )
    api_key = api_key_repository.get(db, id=unsafe_api_key.id)
    assert api_key
    assert api_key.is_active

    api_key = api_key_repository.mark_as_inactive(db, api_key_obj=api_key)
    assert not api_key.is_active

    api_key = api_key_repository.mark_as_active(db, api_key_obj=api_key)
    assert api_key.is_active


def test_get_all_with_user_id(db: Session):
    user = create_agent_user(db)
    api_key = api_key_repository.create(
        db, api_key_obj=APIKeyCreate(name=random_string(10), user_id=user.id)
    )

    api_keys = api_key_repository.get_all_with_user_id(db, user_id=user.id)

    assert len(api_keys) == 1
    assert api_keys[0].id == api_key.id


def test_verify_api_key_with_valid_plain_text_api_key(db: Session):
    user = get_default_agent_user(db)
    unsafe_api_key = api_key_repository.create(
        db, api_key_obj=APIKeyCreate(name=random_string(10), user_id=user.id)
    )
    plain_text_api_key = unsafe_api_key.plain_api_key

    assert api_key_repository.verify_api_key(db, plain_api_key=plain_text_api_key)


def test_verify_api_key_with_invalid_plain_text_api_key_returns_false(db: Session):
    user = get_default_agent_user(db)
    unsafe_api_key = api_key_repository.create(
        db, api_key_obj=APIKeyCreate(name=random_string(10), user_id=user.id)
    )
    plain_text_api_key = unsafe_api_key.plain_api_key + "some extra chars"

    assert not api_key_repository.verify_api_key(db, plain_api_key=plain_text_api_key)

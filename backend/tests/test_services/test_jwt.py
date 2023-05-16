from sqlalchemy.orm.session import Session
from backend.app.schemas.user import UserCreate
import pytest
from backend.app.models import User
from backend.app.services.jwt import get_id_from_token
from datetime import timedelta
from backend.app.api.errors.exceptions import InvalidTokenException

from random import randint


def test_get_id_from_valid_token(db: Session):
    user = User()
    user.id = randint(1, 10000)
    user.is_active = True
    token = user.generate_jwt()

    assert get_id_from_token(token) == user.id


def test_get_id_from_invalid_token():
    with pytest.raises(ValueError):
        get_id_from_token("some invalid token")


def test_get_id_from_expired_token(db: Session):
    user = User()
    user.id = randint(1, 10000)
    user.is_active = True

    token = user.generate_jwt(expires_delta=timedelta(0))

    with pytest.raises(InvalidTokenException):
        get_id_from_token(token)


def test_generate_jwt_for_active_user_succeeds(db: Session):
    user = User()
    user.id = randint(1, 10000)
    user.is_active = True

    token = user.generate_jwt()
    assert token
    assert get_id_from_token(token) == user.id


def test_generate_jwt_from_inactive_user_fails(db: Session):
    user = User()
    user.id = randint(1, 10000)

    assert not user.is_active

    with pytest.raises(Exception):
        user.generate_jwt()

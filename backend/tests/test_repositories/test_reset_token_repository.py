from datetime import datetime, timedelta

from backend.app.core.settings import settings
from backend.app.db.repositories.reset_token import reset_token_repo
from backend.app.models.reset_token import PasswordResetToken
from backend.app.schemas.reset_token import ResetTokenCreate
from backend.tests.utils import get_default_superuser, random_string
from sqlalchemy.orm import Session


RESET_TOKEN_EXPIRE_MINUTES = settings.RESET_TOKEN_EXPIRE_MINUTES


def test_create_reset_token(db: Session):
    user = get_default_superuser(db)
    expiration_time = timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES) + datetime.now()
    token = reset_token_repo.create(
        db,
        obj_in=ResetTokenCreate(
            user_id=user.id, token=random_string(), expires_at=expiration_time
        ),
    )
    assert token
    assert token.user is user
    assert token is reset_token_repo.get(db, id=token.id)


def test_use_reset_token(db: Session):
    user = get_default_superuser(db)
    expiration_time = timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES) + datetime.now()
    token = reset_token_repo.create(
        db,
        obj_in=ResetTokenCreate(
            user_id=user.id, token=random_string(), expires_at=expiration_time
        ),
    )
    assert token
    assert not token.used

    token = reset_token_repo.mark_as_used(db, token_obj=token)
    assert token.used

from backend.app.models.reset_token import PasswordResetToken
from backend.app.db.repositories.base import Base
from sqlalchemy.orm import Session
from sqlalchemy.sql import func


class ResetTokenRepository(Base[PasswordResetToken]):
    def mark_as_used(
        self, db: Session, *, token_obj: PasswordResetToken
    ) -> PasswordResetToken:
        token_obj.used_at = func.now()
        return self.update(db, db_obj=token_obj, obj_in={})


reset_token_repo = ResetTokenRepository(PasswordResetToken)

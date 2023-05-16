from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import String
from backend.app.db.base_class import Base


class PasswordResetToken(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="password_reset_tokens")
    token = Column(String, nullable=False)
    used_at = Column(DateTime)
    expires_at = Column(DateTime, nullable=False)

    @property
    def used(self) -> bool:
        return bool(self.used_at)
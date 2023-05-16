from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Boolean
from backend.app.db.base_class import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

import secrets


class APIKey(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    hashed_key = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="api_keys")

    @staticmethod
    def generate_key():
        KEY_LENGTH = 32
        return secrets.token_urlsafe(KEY_LENGTH)

from backend.app.db.base_class import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship


class UserType(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    users = relationship("User", back_populates="user_type")
    user_history = relationship("UserHistory", back_populates='user_type')
    # agents= relationship("Agent", back_populates='user_type')

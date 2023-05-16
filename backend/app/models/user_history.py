from sqlalchemy import Boolean, Column,ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from backend.app.db.base_class import Base


class UserHistory(Base):
    # __tablename__="user_history"
    id=Column(Integer, primary_key=True, index=True)
    user_id=Column(Integer, ForeignKey("user.id"), nullable=False)
    agent_id=Column(Integer, ForeignKey("agent.id"), nullable=False)
    user_type_id = Column(Integer, ForeignKey('usertype.id'), nullable=False)
    user=relationship('User', back_populates='user_history')
    agent = relationship('Agent', back_populates='user_history')
    user_type = relationship("UserType",back_populates='user_history' )
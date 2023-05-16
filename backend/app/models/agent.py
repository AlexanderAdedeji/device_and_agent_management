from datetime import datetime, timedelta
from backend.app.schemas.reset_token import ResetTokenCreate
import jwt
from sqlalchemy.orm.session import Session
from backend.app.core.settings import settings
from backend.app.db.base_class import Base
from backend.app.schemas.jwt import JWTUser
from backend.app.services import email, security
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from backend.app.schemas.email import ResetPasswordEmailTemplateVariables
from backend.app.models.device import device_user_link
from backend.app.models.reset_token import PasswordResetToken
from backend.app.db.repositories.reset_token import reset_token_repo
from backend.app.models.user import User

JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_EXPIRE_MINUTES = settings.JWT_EXPIRE_MINUTES
RESET_PASSWORD_URL = settings.RESET_PASSWORD_URL
RESET_PASSWORD_TEMPLATE_ID = settings.RESET_PASSWORD_TEMPLATE_ID
SECRET_KEY = settings.SECRET_KEY
SUPERUSER_USER_TYPE = settings.SUPERUSER_USER_TYPE
RESET_TOKEN_EXPIRE_MINUTES = settings.RESET_TOKEN_EXPIRE_MINUTES



class Agent(Base):
    __tablename__ = "agent"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    address = Column(String, nullable=False)
    # is_active = Column(Boolean(), default=False)
    created_by_id = Column(Integer, ForeignKey("user.id"))
    created_by= relationship('User', foreign_keys=[created_by_id])
    # created_by = relationship(
    #     lambda: User, remote_side=id, backref="sub_users", foreign_keys=[created_by_id]
    # )
    user_type_id = Column(Integer, ForeignKey("usertype.id"), nullable=False)
    user_type = relationship("UserType",foreign_keys=[user_type_id])
    user_history=relationship('UserHistory', back_populates='agent')
    # devices = relationship(
    #     "Device", secondary=device_user_link, back_populates="assigned_users"
    # )


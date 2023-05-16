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

JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_EXPIRE_MINUTES = settings.JWT_EXPIRE_MINUTES
RESET_PASSWORD_URL = settings.RESET_PASSWORD_URL
RESET_PASSWORD_TEMPLATE_ID = settings.RESET_PASSWORD_TEMPLATE_ID
SECRET_KEY = settings.SECRET_KEY
SUPERUSER_USER_TYPE = settings.SUPERUSER_USER_TYPE
RESET_TOKEN_EXPIRE_MINUTES = settings.RESET_TOKEN_EXPIRE_MINUTES


# docker-compose -f docker-compose-dev.yml run --publish 6543:5432 database
class User(Base):
    __tablename__="user"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    lasrra_id = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    address = Column(String, nullable=False)
    is_active = Column(Boolean(), default=False)
    deleted = Column(Boolean(), default=False)
    created_by_id = Column(Integer, ForeignKey("user.id"))
    created_by = relationship(
        lambda: User, remote_side=id, backref="sub_users", foreign_keys=[created_by_id]
    )

    agent_id = Column(Integer, ForeignKey("agent.id"))
    agent=relationship('Agent', foreign_keys=[agent_id])

    user_type_id = Column(Integer, ForeignKey("usertype.id"), nullable=False)
    user_type = relationship("UserType", back_populates="users")
    user_history = relationship("UserHistory", back_populates='user')

    devices = relationship(
        "Device", secondary=device_user_link, back_populates="assigned_users"
    )

    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")

    api_keys = relationship("APIKey", back_populates="user")

    @property
    def is_superuser(self):
        return self.user_type.name == SUPERUSER_USER_TYPE

    def set_password(self, password: str) -> None:
        self.hashed_password = security.get_password_hash(password)

    def verify_password(self, password: str) -> bool:
        return security.verify_password(password, self.hashed_password)

    def generate_jwt(self, expires_delta: timedelta = None):
        if not self.is_active:
            raise Exception("user is not active")

        jwt_content = JWTUser(id=self.id).dict()
        if expires_delta is None:
            expires_delta = timedelta(minutes=JWT_EXPIRE_MINUTES)

        now = datetime.now()
        expires_at = now + expires_delta

        jwt_content["exp"] = expires_at.timestamp()
        jwt_content["iat"] = now.timestamp()

        encoded_token = jwt.encode(
            payload=jwt_content, key=str(SECRET_KEY), algorithm=JWT_ALGORITHM
        )
        return encoded_token.decode()

    def generate_password_reset_token(
        self, db: Session, expires_delta: timedelta = None
    ) -> PasswordResetToken:
        token = security.generate_reset_token(self.email)
        if expires_delta is None:
            expires_delta = timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)

        reset_token = reset_token_repo.create(
            db,
            obj_in=ResetTokenCreate(
                user_id=self.id, token=token, expires_at=datetime.now() + expires_delta
            ),
        )

        return reset_token
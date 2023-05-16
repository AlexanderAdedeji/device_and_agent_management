from backend.app.models.user_type import UserType
from backend.app.models.device import Device
from backend.app.schemas.email import EmailTemplateVariables
from typing import Any, Dict, List, Optional, Union

from backend.app.core.settings import settings
from backend.app.models.user import User
from backend.app.db.repositories.base import Base
from backend.app.db.repositories.user_type import user_type as user_type_repo
from backend.app.schemas.user import UserCreate, UserUpdate
from backend.app.services import email
from backend.app.services.security import get_password_hash
from sqlalchemy.orm import Session

REGULAR_USER_TYPE = settings.REGULAR_USER_TYPE
SUPERUSER_USER_TYPE = settings.SUPERUSER_USER_TYPE
USER_TYPES = settings.USER_TYPES
ACTIVATE_ACCOUNT_TEMPLATE_ID = settings.ACTIVATE_ACCOUNT_TEMPLATE_ID
DEACTIVATE_ACCOUNT_TEMPLATE_ID = settings.DEACTIVATE_ACCOUNT_TEMPLATE_ID
CREATE_ACCOUNT_TEMPLATE_ID = settings.CREATE_ACCOUNT_TEMPLATE_ID


class UserRepository(Base[User]):
    def get_by_email(self, db: Session, *, email: str) -> User:
        user = db.query(User).filter(User.email == email).first()
        return user

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            email=obj_in.email,
            phone=obj_in.phone,
            lasrra_id=obj_in.lasrra_id,
            address=obj_in.address,
            agent_id=obj_in.agent_id,
            user_type_id=obj_in.user_type_id,
            created_by_id=obj_in.created_by_id,
        )
        
        db_obj.set_password(obj_in.password)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not user.verify_password(password):
            return None
        return user

    def activate(self, db: Session, *, db_obj: User) -> User:
        return self._set_activation_status(db=db, db_obj=db_obj, status=True)

    def deactivate(self, db: Session, *, db_obj: User) -> User:
        return self._set_activation_status(db=db, db_obj=db_obj, status=False)

    def _set_activation_status(
        self, db: Session, *, db_obj: User, status: bool
    ) -> User:
        if db_obj.is_active == status:
            return db_obj
        return super().update(db, db_obj=db_obj, obj_in={"is_active": status})

    def get_all_devices_assigned_to_user_with_user_id(
        self, db: Session, *, user_id: int
    ) -> List[Device]:
        user = self.get(db, id=user_id)
        return user.devices

    def get_all_users_with_agent_id(self, db: Session, *, agent_id: int) -> List[User]:
        return db.query(self.model).filter(User.agent_id == agent_id).all()

    def set_as_superuser(self, db: Session, db_obj: User) -> User:
        superuser_type = user_type_repo.get_by_name(
            db, name=USER_TYPES[SUPERUSER_USER_TYPE]
        )
        return self.set_usertype(db, db_obj=db_obj, user_type=superuser_type)

    def set_usertype(self, db: Session, db_obj: User, user_type: UserType) -> User:
        db_obj.user_type = user_type
        return super().update(db, db_obj=db_obj, obj_in={})


user_repo = UserRepository(User)

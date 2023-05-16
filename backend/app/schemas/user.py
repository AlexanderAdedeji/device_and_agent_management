from typing import List, Optional

from pydantic import BaseModel, EmailStr, validator

from backend.app.schemas.user_type import UserTypeInDB
from backend.app.schemas.device import DeviceInDB
from commonlib.models import Base
from commonlib.validators import lasrra as lasrra_validators

from backend.app.services.validators import phone as phone_validators


class User(BaseModel):
    first_name: str
    last_name: str
    address: str
    phone: str


class UserCreate(User):
    email: EmailStr
    password: str
    lasrra_id: str
    user_type_id: int
    created_by_id: Optional[int]
    agent_id: Optional[int]

    @validator("lasrra_id")
    def vaildate_lasrra_id(cls, value: str) -> str:
        return lasrra_validators.validate_lasrra_id(value)

    @validator("phone")
    def validate_phone(cls, value: str) -> str:
        return phone_validators.validate_phone_number(value)


class UserUpdate(User):
    email: Optional[EmailStr]
    first_name: Optional[str]
    last_name: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    password: Optional[str] = None


class UserInLogin(BaseModel):
    email: EmailStr
    password: str


class UserWithToken(BaseModel):
    email: EmailStr
    user_type: UserTypeInDB
    agent_name:Optional[str]
    agent_id:Optional[int]
    token: str


class UserCreateForm(User):
    email: EmailStr
    password: str
    lasrra_id: str
    user_type_id:int


class MangerCreateForm(User):
    email: EmailStr
    password: str
    lasrra_id: str
    agent_id:int

class AgentEmployeeUserCreateForm(UserCreateForm):
    agent_id: int


class UserInResponse(User):
    id: int
    email: EmailStr
    lasrra_id: str
    is_active: bool
    is_superuser: bool
    user_type: UserTypeInDB
    created_by_id: Optional[int]
    agent_id: Optional[int]
    agent_name: Optional[str]


class SlimUserInResponse(BaseModel):
    id: int
    email: EmailStr
    lasrra_id: str
    user_type: UserTypeInDB


class ResetPasswordSchema(BaseModel):
    token: str
    password: str


class AgentProfile(BaseModel):
    agent: UserInResponse
    devices: List[DeviceInDB]
    employees: List[UserInResponse]
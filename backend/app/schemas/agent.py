from typing import List, Optional

from pydantic import BaseModel, EmailStr, validator
from backend.app.schemas.user import UserInResponse

from backend.app.schemas.user_type import UserTypeInDB
from backend.app.schemas.device import DeviceInDB
from commonlib.models import Base
from commonlib.validators import lasrra as lasrra_validators
from backend.app.services.validators import phone as phone_validators



class Agent(BaseModel):
    name:str
    email:EmailStr
    

class AgentCreateForm(Agent):
    address: str



class AgentCreate(Agent):
    address: str
    user_type_id: int
    created_by_id: Optional[int]

class AgentUpdate:
    email: Optional[EmailStr]
    address: Optional[str]


class AgentInResponse(Agent):
    id: int
    email: EmailStr
    address:str
    user_type: UserTypeInDB
    created_by_id: Optional[int]
    agent_id: Optional[int]

class AgentProfile(BaseModel):
    agent: AgentInResponse
    devices: List[DeviceInDB]
    employees: List[UserInResponse]



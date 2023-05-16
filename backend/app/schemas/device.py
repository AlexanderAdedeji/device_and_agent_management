from typing import List, Optional
from pydantic import BaseModel
from pydantic.networks import EmailStr


class Device(BaseModel):
    name: str
    mac_id: str
    creator_id: int


class DeviceCreate(Device):
    agent_id: int


class DeviceInBody(BaseModel):
    name: str
    mac_id: str
    agent_id: int


class DeviceUpdate(BaseModel):
    mac_id: str


class DeviceUser(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    address: str
    lasrra_id: str
    hashed_password: str
    is_active: bool
    created_by_id: Optional[int]
    agent_id: Optional[int]

class DeviceAgent(BaseModel):
    id: int
    name: str
    email: EmailStr
    address: str



class DeviceUserUpdate(BaseModel):
    password: str


class DeviceConfig(BaseModel):
    device_id: int
    is_active: bool
    rabbitmq_uri: str
    api_base_uri: str
    secret_key: str


class DeviceMetaData(BaseModel):
    config: DeviceConfig
    assigned_users: List[DeviceUser]
    agent: Optional[DeviceAgent]


class DeviceInDB(Device):
    id: int
    is_active: bool
    agent_id: int
    agent_name:Optional[str]
    assigned_users: List

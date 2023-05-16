from pydantic import BaseModel


class APIKey(BaseModel):
    name: str


class APIKeyInResponse(APIKey):
    id: int
    is_active: bool


class APIKeyCreate(APIKey):
    user_id: int


class UnsafeAPIKey(APIKeyCreate):
    id: int
    is_active: bool
    plain_api_key: str

from datetime import datetime

from pydantic import BaseModel, EmailStr


class JWTUser(BaseModel):
    id: int


class JWTMeta(BaseModel):
    exp: datetime
    sub: str
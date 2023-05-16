from datetime import datetime
from pydantic import BaseModel


class ResetToken(BaseModel):
    user_id: int
    token: str
    expires_at: datetime


class ResetTokenCreate(ResetToken):
    pass
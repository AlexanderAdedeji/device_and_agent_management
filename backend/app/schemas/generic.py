from typing import List
from pydantic import BaseModel


class GenericMessageResponse(BaseModel):
    message: str

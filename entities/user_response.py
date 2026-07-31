from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserResponse(BaseModel):
    id: str = Field(..., min_length=1)
    email: str
    fullName: str
    roles: list[str]
    verified: bool = False
    banned: bool = False
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
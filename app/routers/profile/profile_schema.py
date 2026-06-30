from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from app.models.user import UserRole

class ProfileOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    avatar: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zipCode: Optional[str] = None

class AvatarOut(BaseModel):
    avatar: str
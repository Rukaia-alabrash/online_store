from datetime import datetime
from app.models.user import UserRole
from pydantic import BaseModel 
from typing import Optional

# Pydantic model for user output, including fields for ID, name, email, role, avatar, and creation date, with ORM mode enabled for compatibility with SQLAlchemy models.
class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    avatar : Optional[str] = None
    created_at: datetime

    
    model_config = {"from_attributes": True}  
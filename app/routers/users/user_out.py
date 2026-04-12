from xmlrpc.client import DateTime

from app.models.user import UserRole
from pydantic import BaseModel 

# Pydantic model for user output, including fields for ID, name, email, role, avatar, and creation date, with ORM mode enabled for compatibility with SQLAlchemy models.
class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    avatar : str
    createdAt: DateTime

    class Config:
        orm_mode = True
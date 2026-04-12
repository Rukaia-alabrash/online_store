from xmlrpc.client import DateTime

from app.models.user import UserRole
from pydantic import BaseModel 


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    avater : str
    createdAt: DateTime

    class Config:
        orm_mode = True
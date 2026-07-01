from alembic.environment import Optional
from pydantic import BaseModel
from app.models.user import  UserRole
from app.routers.shared.pagination import Pagination
from datetime import datetime

class Update_user_body(BaseModel):
    name : Optional[str] = None
    email : Optional[str] = None
    avatar : Optional[str] = None
    role : Optional[UserRole] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    avatar : Optional[str] = None
    created_at: datetime

    
    model_config = {"from_attributes": True}  


class PaginationUser(BaseModel):
    users: list[UserOut]
    pagination: Pagination
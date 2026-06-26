from alembic.environment import Optional
from pydantic import BaseModel
from app.models.user import  UserRole
from app.routers.shared.pagination import Pagination
from datetime import datetime

# Pydantic model for updating user details, with optional fields for name, email, avatar, and role
class Update_user_body(BaseModel):
    name : Optional[str] = None
    email : Optional[str] = None
    avatar : Optional[str] = None
    role : Optional[UserRole] = None


# Pydantic model for user output, including fields for ID, name, email, role, avatar, and creation date, with ORM mode enabled for compatibility with SQLAlchemy models.
class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    avatar : Optional[str] = None
    created_at: datetime

    
    model_config = {"from_attributes": True}  


# Pydantic model for paginated response containing a list of users and pagination metadata
class PaginationUser(BaseModel):
    users: list[UserOut]
    pagination: Pagination
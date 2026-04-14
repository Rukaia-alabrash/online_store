from alembic.environment import Optional
from pydantic import BaseModel
from app.models.user import  UserRole

# Pydantic model for updating user details, with optional fields for name, email, avatar, and role
class Update_user_body(BaseModel):
    name : Optional[str] = None
    email : Optional[str] = None
    avatar : Optional[str] = None
    role : Optional[UserRole] = None
from pydantic import BaseModel
from app.models import user
from app.routers.users import user_out
from app.routers.users.user_out import UserOut
from app.routers.shared.pagination import Pagination

# Pydantic model for paginated response containing a list of users and pagination metadata
class PaginationUser(BaseModel):
    users: list[UserOut]
    pagination: Pagination
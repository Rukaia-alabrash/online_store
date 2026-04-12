from pydantic import BaseModel
from app.routers.users.user_routers import user_out
from app.routers.shared.pagination import Pagination

# Pydantic model for paginated response containing a list of users and pagination metadata
class PaginationUser(BaseModel):
    list: list[user_out.UserOut]
    pagination: Pagination
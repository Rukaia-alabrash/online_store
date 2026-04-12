from pydantic import BaseModel
from app.routers.users.user_routers import user_out

class Pagination(BaseModel):
    page: int 
    limit: int 
    total: int 
    totalPages: int

class PaginationUser(BaseModel):
    list: list[user_out.UserOut]
    pagination: Pagination
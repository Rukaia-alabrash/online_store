from pydantic import BaseModel


# Pydantic models for pagination response, including metadata about the current page, total items, and total pages, as well as a list of user data for the current page.
class Pagination(BaseModel):
    page: int 
    limit: int 
    total: int 
    totalPages: int
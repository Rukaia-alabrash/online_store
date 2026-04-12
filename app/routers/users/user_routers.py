from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query 
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import require_admin, get_current_user
from app.models.user import User , UserRole 
from app.routers.shared.auth_service import AuthService
from app.routers.users import pagination_user, user_out,user_shema
from app.routers.users.user_service import BasicService, UserReader, UserWriter 
import math

router = APIRouter(prefix="/users", tags=["users"])

# Get users with pagination, filtering by role and searching by name or email
@router.get("/", response_model=pagination_user.PaginationUser)
def get_users(page: int = Query(1,ge=1), 
            limit: int = Query(10, ge=1, le=100),
            role: Optional[UserRole] = None,
            search: Optional[str] = None,
            db: Session = Depends(get_db),
            current_user: User = Depends(require_admin)):
    
    # using UserReader to filter users by role and search term (name or email)
    service = UserReader(db)
    query = service.get_filter_user(role=role, search=search)

    # Calculate total users and total pages for pagination
    total = query.count()
    total_pages = math.ceil(total / limit) if total > 0 else 0
    users = query.limit(limit).offset((page-1)*limit).all()

    # Return paginated response with user data and pagination metadata
    return pagination_user.PaginationUser(
        users=[user_out.UserOut.from_orm(user) for user in users],
        pagination=pagination_user.Pagination(
            page=page,
            limit=limit,
            total=total,
            totalPages=total_pages
        )
    )

# Put endpoint to update user details, only accessible by the user themselves or an admin
@router.put("/{id}", response_model=user_out.UserOut)
def update_user(id : int ,
                current_user: User =Depends(get_current_user),
                db: Session = Depends(get_db),
                body: user_shema.Update_user_body = Depends()):
    
    # Check if the current user has permission to modify the target user (details) using the AuthService
    auth_service = AuthService(db)
    auth_service.can_modify_user(current_user, id)

    # Update the user details using the UserWriter service
    service = UserWriter(db)
    user = service.update_user(id=id, current_user=current_user, name=body.name, email=body.email, avatar=body.avatar, role=body.role)
    
    return user_out.UserOut.from_orm(user)

# Delete endpoint to remove a user, only accessible by admins
@router.delete("/{id}")
def delete_user(id : int ,
                current_user: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    
    #Delete the user using the UserWriter service
    service = UserWriter(db)
    service.delete_user(id=id, current_user=current_user)

    return True
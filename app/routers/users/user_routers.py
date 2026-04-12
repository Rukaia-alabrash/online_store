import email
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query 
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User , UserRole 
from app.routers.users import user_out,pagination, user_update
import math

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=pagination.PaginationUser)
def get_users(page: int = Query(1,ge=1), 
            limit: int = Query(10, ge=1, le=100),
            role: Optional[UserRole] = None,
            search: Optional[str] = None,
            db: Session = Depends(get_db),
            current_user: User = Depends(require_admin)):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if search:
        query = query.filter(
            or_(User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")))
    query = query.order_by(User.created_at.desc(),User.id.desc())
    total = query.count()
    total_pages = math.ceil(total / limit) if total > 0 else 0
    users = query.limit(limit).offset((page-1)*limit).all()
    return pagination.PaginationUser(
        users=[user_out.UserOut.from_orm(user) for user in users],
        pagination=pagination.Pagination(
            page=page,
            limit=limit,
            total=total,
            totalPages=total_pages
        )
    )

@router.put("/", response_model=user_update.UserUpdate)
def update_user(id : int ,
                current_user: User =Depends(require_admin),
                db: Session = Depends(get_db),
                name : Optional[str] = None,
                email : Optional[str] = None,
                avatar : Optional[str] = None,
                role : Optional[UserRole] = None):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
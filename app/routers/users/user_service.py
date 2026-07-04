from fastapi import HTTPException, Depends
from app.database import get_db
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from typing import Optional
from sqlalchemy import or_


class BasicService:
    def __init__(self, db: Session):
        self.db = db

    def cheack_user_exists(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user


class UserReader(BasicService):
    def get_filter_user(self,
                         role: Optional[UserRole] = None,
                         search: Optional[str] = None,
                         include_inactive: bool = False):
        query = self.db.query(User)

        # Hide soft-deleted users by default (e.g. from admin list, search)
        if not include_inactive:
            query = query.filter(User.is_active == True)

        if role:
            query = query.filter(User.role == role)
        if search:
            query = query.filter(
                or_(User.name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")))
        return query.order_by(User.created_at.desc(), User.id.desc())


class UserWriter(BasicService):

    def update_user(self,
                     id: int,
                     current_user: User,
                     name: Optional[str] = None,
                     email: Optional[str] = None,
                     avatar: Optional[str] = None,
                     role: Optional[UserRole] = None):

        user = self.cheack_user_exists(id)

        if name:
            user.name = name
        if email:
            user.email = email
        if avatar:
            user.avatar = avatar
        if role:
            if current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Forbidden")
            user.role = role

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, id: int):
        """Soft delete: deactivate the user instead of removing the row.
        Keeps receipts, payments, reviews, etc. intact for records/auditing.
        """
        user = self.cheack_user_exists(id)

        if not user.is_active:
            raise HTTPException(status_code=400, detail="User is already deactivated")

        user.is_active = False
        self.db.commit()
        self.db.refresh(user)

        return True

    def reactivate_user(self, id: int):
        """Optional: allow an admin to restore a soft-deleted user."""
        user = self.cheack_user_exists(id)

        if user.is_active:
            raise HTTPException(status_code=400, detail="User is already active")

        user.is_active = True
        self.db.commit()
        self.db.refresh(user)

        return user
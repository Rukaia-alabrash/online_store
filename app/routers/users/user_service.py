from fastapi import HTTPException , Depends
from app.models import user
from app.database import get_db
from app.models import user
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from typing import Optional
from sqlalchemy import or_


class BasicService :
    def __init__(self, db:Session):
        self.db = db 

    # Method to check if a user exists by their ID, raising a 404 error if not found
    def cheack_user_exists(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

# UserReader class to handle reading user data with optional filtering by role and search term (name or email)
class UserReader (BasicService):
    def get_filter_user(self, 
                        role: Optional[UserRole] = None,
                        search: Optional[str] = None):
        query = self.db.query(User)
        if role:
            query = query.filter(User.role == role)
        if search:
            query = query.filter(
            or_(User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")))
        return query.order_by(User.created_at.desc(),User.id.desc())

# UserWriter class to handle updating and deleting user details, with authorization checks for modifying user roles
class UserWriter(BasicService):

    # Method to update user details, allowing changes to name, email, avatar, and role (with role changes restricted to admins)
    def update_user(self,
                    id:int ,
                    current_user : User,
                    name : Optional[str] = None,
                email : Optional[str] = None,
                avatar : Optional[str] = None,
                role : Optional[UserRole] = None):
        
        user= self.cheack_user_exists(id)

        if name :
            user.name=name

        if email :
            user.email=email

        if avatar :
            user.avatar=avatar

        if role :
            if current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Forbidden")
            user.role=role

        self.db.commit()
        self.db.refresh(user)
        
        return user
    # Method to delete a user by their ID, with a check to ensure the user exists before deletion
    def delete_user(self,
                    id:int):
        user = self.cheack_user_exists(id)
        self.db.delete(user)
        self.db.commit()

        return True
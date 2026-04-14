from app.dependencies import get_db, get_current_user, require_admin
from app.models.user import User, UserRole
from sqlalchemy.orm import Session
from fastapi import HTTPException

# Service class to handle authorization logic related to user modifications
class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    # Method to check if the current user has permission to modify the target user
    def can_modify_user(self, current_user: User, target_user_id: int) -> bool:
        if current_user.id != target_user_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        return True
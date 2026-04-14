from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from app.database import get_db
<<<<<<< HEAD
from app.models.user import User , UserRole
=======
from app.models.user import User, UserRole
>>>>>>> 9837e79ab1480042f0174514e17e5d8af7930f26

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

security = HTTPBearer(auto_error=True)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    # Extract the token from the Authorization header
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = int(user_id)

    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

<<<<<<< HEAD
def get_current_admin(current_user: User = Depends(get_current_user)):
    if not current_user.role == UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not enough permissions")
    return current_user

# Dependency to check if the user has admin privileges
def require_admin(current_user:User=Depends(get_current_user)):
    if current_user.role  != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user  

=======

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role.value.lower() != "admin":
        print(current_user.role.value)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return True
>>>>>>> 7bc2e40e79bec43af059136fce9cd147f0d6f29a

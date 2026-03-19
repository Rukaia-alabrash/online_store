# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas import LoginRequest , RegisterRequest

#read .env file
load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

#bcypt password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "1440"))

#-------------- jwt token functions --------------
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



#-------------- Login --------------
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not pwd_context.verify(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "avatar": user.avatar or ""
        },
        "token": access_token,
        "refreshToken": refresh_token
    }


#-------------- Register --------------
@router.post("/register", status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):

    # 1. check if user exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")

    # 2. hash password
    hashed_password = pwd_context.hash(data.password)

    # 3. create user
    new_user = User(
        name=data.name,
        email=data.email,
        password=hashed_password,
        role=UserRole.USER,
        avatar=""
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 4. tokens
    access_token = create_access_token({"sub": str(new_user.id)})
    refresh_token = create_refresh_token({"sub": str(new_user.id)})

    # 5. response
    return {
        "user": {
            "id": str(new_user.id),
            "name": new_user.name,
            "email": new_user.email,
            "role": "user",
            "avatar": ""
        },
        "token": access_token,
        "refreshToken": refresh_token
    }

@router.post("/logout")
def logout():
    # For JWT, logout is typically handled on the client side by deleting the token.
    # Optionally, you can implement token blacklisting on the server side.
    return {"message": "Logged out successfully"}

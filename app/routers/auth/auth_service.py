from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
from collections import defaultdict

from app.models.user import User, UserRole
from app.core.security import hash_password, verify_password, validate_password
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ChangePasswordRequest,
    ResetPasswordRequest,
)
from app.utils.email_sender import send_password_reset_email
from fastapi import BackgroundTasks

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "1440"))


# -------------- Rate Limiter (In-Memory) --------------
# { email: {"attempts": int, "window_start": datetime} }
_login_attempts: dict = defaultdict(lambda: {"attempts": 0, "window_start": None})

MAX_ATTEMPTS = 3
WINDOW_SECONDS = 60


def _check_rate_limit(email: str):
    now = datetime.now(timezone.utc)
    record = _login_attempts[email]

    # أول مرة أو انتهت الدقيقة — بنرجع النافذة
    if record["window_start"] is None or (now - record["window_start"]).seconds >= WINDOW_SECONDS:
        record["attempts"] = 0
        record["window_start"] = now

    if record["attempts"] >= MAX_ATTEMPTS:
        seconds_passed = (now - record["window_start"]).seconds
        wait = WINDOW_SECONDS - seconds_passed
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Try again in {wait} seconds."
        )


def _increment_attempts(email: str):
    _login_attempts[email]["attempts"] += 1


def _reset_attempts(email: str):
    _login_attempts[email] = {"attempts": 0, "window_start": None}


# -------------- Token Helpers --------------

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_password_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {"sub": email, "exp": expire, "type": "reset"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _build_auth_response(user: User) -> dict:
    """بناء الـ response الموحد للـ login و register"""
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return {
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "avatar": user.avatar or "",
        },
        "token": access_token,
        "refreshToken": refresh_token,
    }


# -------------- Services --------------

def login_user(data: LoginRequest, db: Session) -> dict:
    _check_rate_limit(data.email)

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        _increment_attempts(data.email)
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.password, user.password):
        _increment_attempts(data.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    _reset_attempts(data.email)
    return _build_auth_response(user)


def register_user(data: RegisterRequest, db: Session) -> dict:
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    new_user = User(
        name=data.name,
        email=data.email,
        password=hash_password(data.password),
        role=UserRole.USER,
        avatar="",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return _build_auth_response(new_user)


def refresh_access_token(data: RefreshTokenRequest, db: Session) -> dict:
    try:
        payload = jwt.decode(data.refreshToken, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user_id = int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    return {
        "token": create_access_token({"sub": str(user.id)}),
        "refreshToken": create_refresh_token({"sub": str(user.id)}),
    }


def forgot_password(data: ForgotPasswordRequest, db: Session) -> dict:
    user = db.query(User).filter(User.email == data.email).first()
    if user:
        reset_token = create_password_reset_token(user.email)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        send_password_reset_email(user.email, reset_link)
    return {"message": "If an account with that email exists, a reset link has been sent."}



def reset_password(data: ResetPasswordRequest, db: Session) -> dict:
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        token_type = payload.get("type")
        if email is None or token_type != "reset":
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not validate_password(data.newPassword):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters with uppercase, lowercase, and a digit")

    user.password = hash_password(data.newPassword)
    db.commit()
    return {"message": "Password reset successfully"}


def change_password(data: ChangePasswordRequest, current_user: User, db: Session) -> dict:
    if not verify_password(data.currentPassword, current_user.password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    if not validate_password(data.newPassword):
        raise HTTPException(status_code=400, detail="Invalid new password")

    current_user.password = hash_password(data.newPassword)
    db.commit()
    return {"message": "Password changed successfully"}
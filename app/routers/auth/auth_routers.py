# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas import LoginRequest , RegisterRequest , RefreshTokenRequest , ForgotPasswordRequest , ChangePasswordRequest , VerifyOtpRequest , ResetPasswordRequest
from app.dependencies import get_current_user , require_admin
from app.core.security import hash_password, verify_password, validate_password
from app.models.otp import Otp
import random
from app.core.email import send_otp_email


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


def create_password_reset_token(email: str):
    expire = datetime.now(timezone.utc) + timedelta(hours=1)

    payload = {
        "sub": email,
        "exp": expire,
        "type": "reset"
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


#----------- Generate OTP code -------------
def generate_otp() -> str:
    return str(random.randint(100000, 999999))



#-------------- Login --------------
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")


    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first")


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
    hashed_password = hash_password(data.password)

    # 3. create user
    new_user = User(
        name=data.name,
        email=data.email,
        password=hashed_password,
        role=UserRole.USER,
        avatar="",
        is_verified=False
    )
    db.add(new_user)
    db.flush()  

    # 4. generate OTP
    otp_code = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    otp_entry = Otp(
        user_id=new_user.id,
        otp_code=otp_code,
        expires_at=expires_at
    )
    db.add(otp_entry)

    # 5. send OTP email
    try:
        send_otp_email(new_user.email, otp_code)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to send verification email. Please try again."
        )

    db.commit()
    db.refresh(new_user)

    return {"message": "Account created. Check your email for the verification code."}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    # For JWT, logout is typically handled on the client side by deleting the token.
    # Optionally, you can implement token blacklisting on the server side.
    return {"message": "Logged out successfully"}


#-------------- Refresh Token --------------
@router.post("/refresh")
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):

    refresh_token = data.refreshToken

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user_id = int(user_id)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Generate new tokens
    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "token": new_access_token,
        "refreshToken": new_refresh_token
    }


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    
    # 1. verify token
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        token_type = payload.get("type")

        if email is None or token_type != "reset":
            raise HTTPException(status_code=400, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # 2. find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 3. validate new password
    if not validate_password(data.newPassword):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters with uppercase, lowercase, and a digit")

    # 4. update password
    user.password = hash_password(data.newPassword)
    db.commit()

    return {"message": "Password reset successfully"}


#-------------- Forgot Password --------------
@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if user:
        reset_token = create_password_reset_token(user.email)

        reset_link = f"http://localhost:3000/reset-password?token={reset_token}"

        # In a real application, you would send this link via email to the user.
        print(reset_link)

    return {
        "message": "If an account with that email exists, a reset link has been sent."
    }

#-------------- Change Password --------------  
@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # check current password
    if not verify_password(data.currentPassword, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # validate new password
    if not validate_password(data.newPassword):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid new password"
        )

    # update password
    hashed_password = hash_password(data.newPassword)
    current_user.password = hashed_password

    db.commit()

    return {
        "message": "Password changed successfully"
    }



# ------------- Verify OTP --------------

@router.post("/verify-otp")
def verify_otp(data: VerifyOtpRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # get latest OTP
    otp_entry = (
        db.query(Otp)
        .filter(Otp.user_id == user.id)
        .order_by(Otp.expires_at.desc())
        .first()
    )

    if not otp_entry:
        raise HTTPException(status_code=400, detail="No OTP found")

    if datetime.now(timezone.utc) > otp_entry.expires_at:
        raise HTTPException(status_code=400, detail="OTP expired")

    if otp_entry.otp_code != data.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # mark user as verified
    user.is_verified = True
    db.delete(otp_entry) # delete OTP after successful verification 
    db.commit()

    # return tokens
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


@router.get("/me")
def get_me(admin: User = Depends(require_admin),db: Session = Depends(get_db)):
    return {"message": "hi admin" , "admin": admin.name}



from pydantic import BaseModel, EmailStr , field_validator, model_validator
from pydantic import BaseModel, EmailStr, Field
import re

class LoginRequest(BaseModel):
    email: EmailStr   # validate email format automatically
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)
    confirmPassword: str

    @field_validator("password")
    @classmethod
    def strong_password(cls, v):

        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Must contain lowercase letter")

        if not re.search(r"[0-9]", v):
            raise ValueError("Must contain number")

        return v
    
    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirmPassword:
            raise ValueError("Passwords do not match")
        return self
    
class RefreshTokenRequest(BaseModel):
    refreshToken: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str

    @field_validator("newPassword")
    @classmethod
    def strong_password(cls, v):

        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Must contain lowercase letter")

        if not re.search(r"[0-9]", v):
            raise ValueError("Must contain number")

        return v
  
class ResetPasswordRequest(BaseModel):
    token: str
    newPassword: str

    @field_validator("newPassword")
    @classmethod
    def strong_password(cls, v):

        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Must contain lowercase letter")

        if not re.search(r"[0-9]", v):
            raise ValueError("Must contain number")

        return v
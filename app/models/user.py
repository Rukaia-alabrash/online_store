from sqlalchemy import Column, Integer, Enum, DateTime,  String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    avater = Column(String(1024), nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    cart = relationship("Cart", back_populates="user", uselist=False)
    otps = relationship("Otp", back_populates="user")
    shipping_address = relationship("ShippingAddress", back_populates="user")
    receipts = relationship("Receipt", back_populates="user")
    wishlist = relationship("Wishlist", back_populates="user")
    payments = relationship("Payment", back_populates="user")

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ShippingAddress(Base):
    __tablename__ = "shipping_address"

    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    full_name = Column(String(255),    nullable=False)
    address   = Column(String(255),    nullable=False)
    city      = Column(String(100),    nullable=False)
    zip_code  = Column(Integer, nullable=False)

    # relationships
    user     = relationship("User",    back_populates="shipping_address")
    receipts = relationship("Receipt", back_populates="shipping_address")
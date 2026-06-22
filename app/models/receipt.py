from sqlalchemy import Column, Integer, String, ForeignKey, Enum , Numeric
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class ReceiptStatus(enum.Enum):
    PENDING   = "pending"   
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED   = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Receipt(Base):
    __tablename__ = "receipts"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"),            nullable=False)
    shipping_address_id = Column(Integer, ForeignKey("shipping_address.id"), nullable=False)
    total_price         = Column(Numeric(10,2), nullable=False)
    payment_status      = Column(String(50),    nullable=False)
    status = Column(
    Enum(ReceiptStatus, values_callable=lambda x: [e.value for e in x]),
    nullable=False,
    default=ReceiptStatus.PENDING
)
    # relationships
    user             = relationship("User",           back_populates="receipts")
    shipping_address = relationship("ShippingAddress", back_populates="receipts")
    payment          = relationship("Payment",        back_populates="receipt", uselist=False)
    order_items      = relationship("OrderItem",      back_populates="receipt")
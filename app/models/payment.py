from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PaymentIntentStatus(Enum):
    REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    REQUIRES_ACTION = "requires_action"
    PROCESSING = "processing"
    REQUIRES_CAPTURE = "requires_capture"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"),    nullable=False)
    receipt_id = Column(Integer, ForeignKey("receipts.id"),
                        unique=True, nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String(10),    nullable=False)
    status = Column(Enum(PaymentIntentStatus), nullable=False,
                    default=PaymentIntentStatus.REQUIRES_PAYMENT_METHOD)
    payment_method = Column(String(20),    nullable=False)
    transaction_id = Column(Integer, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    user = relationship("Users",    back_populates="payments")
    receipt = relationship("Receipts", back_populates="payment")

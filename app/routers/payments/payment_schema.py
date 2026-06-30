from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.payment import PaymentIntentStatus
from app.models.receipt import ReceiptStatus


class OrderItemIn(BaseModel):
    productId: int
    quantity: int
    price: float

class ShippingAddressIn(BaseModel):
    fullName: str
    address: str
    city: str
    zipCode: str


class CreatePaymentIntentRequest(BaseModel):
    amount: int           # in cents
    currency: str         # "usd"
    paymentMethodId: str  
    shippingAddress: ShippingAddressIn  
    items: List[OrderItemIn]

class CreatePaymentIntentResponse(BaseModel):
    clientSecret: str
    paymentIntentId: str
    receiptId: int



class OrderItemOut(BaseModel):
    id: int
    productId: int
    price: float
    quantity: float

    class Config:
        from_attributes = True


class PaymentOut(BaseModel):
    id: int
    amount: int
    currency: str
    status: PaymentIntentStatus
    transactionId: Optional[str] = None
    createdAt: datetime

    class Config:
        from_attributes = True


class ReceiptOut(BaseModel):
    id: int
    totalPrice: int
    status: ReceiptStatus
    paymentStatus: str
    orderItems: List[OrderItemOut]
    payment: Optional[PaymentOut] = None
    createdAt: Optional[datetime] = None

    class Config:
        from_attributes = True
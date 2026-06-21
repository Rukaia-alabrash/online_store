from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.models.receipt import ReceiptStatus
from app.routers.shared.pagination import Pagination


# ---------- Shipping Address ----------

class ShippingAddressOut(BaseModel):
    fullName: str
    email: str
    address: str
    city: str
    zipCode: str

    model_config = {"from_attributes": True}


class ShippingAddressIn(BaseModel):
    fullName: str
    email: str
    address: str
    city: str
    zipCode: str


# ---------- Order Item ----------

class OrderItemOut(BaseModel):
    id: str            # product_id, converted to string per project convention
    price: float
    quantity: int

    model_config = {"from_attributes": True}


class OrderItemIn(BaseModel):
    id: str            # product_id sent by frontend, as string
    price: float
    quantity: int


# ---------- Order (Receipt) ----------

class OrderOut(BaseModel):
    id: str
    userId: str
    items: List[OrderItemOut]
    total: float  # total_price is Numeric(10,2) in DB now, no cents conversion needed
    status: str
    shippingAddress: ShippingAddressOut
    createdAt: datetime
    updatedAt: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    userId: str
    items: List[OrderItemIn]
    total: float
    shippingAddress: ShippingAddressIn


class UpdateOrderStatusBody(BaseModel):
    status: ReceiptStatus


class PaginatedOrders(BaseModel):
    orders: List[OrderOut]
    pagination: Pagination
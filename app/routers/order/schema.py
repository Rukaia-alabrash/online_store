from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.models.receipt import ReceiptStatus
from app.routers.shared.pagination import Pagination
from pydantic import Field


# ---------- Shipping Address ----------

class ShippingAddressOut(BaseModel):
    full_name: str
    address: str
    city: str
    zip_code: str

    model_config = {"from_attributes": True}


class ShippingAddressIn(BaseModel):
    full_name: str = Field(alias="fullName")
    address: str
    city: str
    zip_code: str = Field(alias="zipCode")

    model_config = {"populate_by_name": True}


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
    user_id: str
    items: List[OrderItemOut]
    total: float  # total_price is Numeric(10,2) in DB now, no cents conversion needed
    status: str
    shipping_address: ShippingAddressOut
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    user_id: str = Field(alias="user_id")
    items: List[OrderItemIn]
    total: float
    shipping_address: ShippingAddressIn = Field(alias="shipping_address")

    model_config = {"populate_by_name": True}


class UpdateOrderStatusBody(BaseModel):
    status: ReceiptStatus


class PaginatedOrders(BaseModel):
    orders: List[OrderOut]
    pagination: Pagination
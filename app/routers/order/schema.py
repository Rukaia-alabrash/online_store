from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.models.receipt import ReceiptStatus
from app.routers.shared.pagination import Pagination


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ShippingAddressOut(CamelModel):
    full_name: str
    email: str
    address: str
    city: str
    zip_code: str


class ShippingAddressIn(CamelModel):
    full_name: str
    email: str
    address: str
    city: str
    zip_code: str

class UserItemOut(CamelModel):
    id: str
    name: str
    price: float
    image: Optional[str] = None
    rating: float
    discount_percentage: Optional[float] = None
    quantity: int
class OrderItemOut(CamelModel):
    id: str
    price: float
    quantity: int


class OrderItemIn(CamelModel):
    id: str
    price: float
    quantity: int


class OrderOut(CamelModel):
    id: str
    user_id: str
    items: List[OrderItemOut]
    total: float
    status: str
    shipping_address: ShippingAddressOut


class OrderCreate(CamelModel):
    user_id: str
    items: List[OrderItemIn]
    total: float
    shipping_address: ShippingAddressIn


class UpdateOrderStatusBody(CamelModel):
    status: ReceiptStatus


class PaginatedOrders(CamelModel):
    orders: List[OrderOut]
    pagination: Pagination
from pydantic import BaseModel
from typing import List


class AddItemRequest(BaseModel):
    product_id: int
    quantity: int = 1


class UpdateItemRequest(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    product_id: int
    name: str
    price: float
    image: str
    quantity: int

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total: float
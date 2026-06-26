from pydantic import BaseModel
from typing import Optional




class FavoriteProduct(BaseModel):
    ProductId: int
    name: str
    price: float
    image: str
    rating: float
    discountPercentage: Optional[float] = None

    class Config:
        from_attributes = True


class FavoriteListOut(BaseModel):
    products: list[FavoriteProduct]

    class Config:
        from_attributes = True

class FavoriteOut(BaseModel):
    id: int
    user_id: int
    product_id: int

    class Config:
        from_attributes = True
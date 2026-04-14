import nh3
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

# iamge
class ImageOut(BaseModel):
    url: str
    is_primary: bool
 
    class Config:
        from_attributes = True
 
#  pagination
class PaginationOut(BaseModel):
    page: int
    limit: int
    total: int
    totalPages: int


# products
class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    price: float
    category: str
    image: str                          # primary image URL
    images: list[str]                   # all image URLs
    rating: float
    reviews: int
    stock: int
    features: list[str]
    discountPercentage: Optional[float] = None
    discountExpiry: Optional[datetime] = None                 # ISO date 
    createdAt: datetime
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True
 
class ProductListOut(BaseModel):
    products: list[ProductOut]
    categories: list[str]
    pagination: PaginationOut

    class Config:
        from_attributes = True

class ProductIn(BaseModel):
    name : str
    description: str
    price: float
    stock: int
    category : str
    features:Optional[list[str]] = None
    discountPercentage: Optional[float] = None
    discountExpiry: Optional[datetime] = None

    @field_validator("discountExpiry", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v
    
    @field_validator("name","description","category")
    @classmethod
    def sanitize_strings(cls,v):
        v = v.strip()
        v = nh3.clean(v,tags=set())
        return v
    
    @field_validator("features")
    @classmethod
    def sanitize_features(cls, v):
        return [
            nh3.clean(feature.strip(), tags = set())
            for feature in v if feature.strip()
        ]

class ProductUpdate(BaseModel):
    name : Optional[str]
    description: Optional[str]
    price: Optional[float]
    stock: Optional[int]
    category : Optional[str]
    features:Optional[list[str]] 
    discountPercentage: Optional[float] 
    discountExpiry: Optional[datetime] 

    @field_validator("discountExpiry", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v
    
    @field_validator("name","description","category")
    @classmethod
    def sanitize_strings(cls,v):
        v = v.strip()
        v = nh3.clean(v,tags=set())
        return v
    
    @field_validator("features")
    @classmethod
    def sanitize_features(cls, v):
        return [
            nh3.clean(feature.strip(), tags = set())
            for feature in v if feature.strip()
        ]
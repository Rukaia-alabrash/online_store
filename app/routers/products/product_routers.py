from fastapi import APIRouter, Depends, HTTPException, Header, status , UploadFile , File
from fastapi.params import  Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin

from typing import Annotated, List

from .product_schema import ProductIn, ProductListOut, ProductOut, ProductUpdate
from .product_service import ProductService



router = APIRouter(prefix="/products",tags=["products"])


@router.get("/", status_code=status.HTTP_200_OK,response_model=ProductListOut)
def list_products(
    accept_language: Annotated[str|None,Header()] = None,
    page: int = Query(1, ge=1),
    limit : int = Query(12, ge=1, le=100),
    category: str = None,
    search: str = None,
    minPrice: float = None,
    maxPrice: float = None,
    rating: float = None,
    sortBy: str = Query(None ,regex="^(name|price|rating)$"),
    sortOrder: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):

    lang = accept_language[:2] if accept_language else "en"
    return ProductService.list_products(lang,page,limit,category,search,minPrice,maxPrice,rating,sortBy,sortOrder,db)


@router.get("/discounted", status_code=status.HTTP_200_OK,response_model=List[ProductOut])
def get_discounted_products(
    accept_language: Annotated[str|None,Header()] = None,
    db: Session = Depends(get_db)
):
    lang = accept_language[:2] if accept_language else "en"
    return ProductService.list_discounted_products(lang,db)


@router.get("/{product_id}", status_code=status.HTTP_200_OK,response_model=ProductOut)
def get_product(
    product_id: int,
    accept_language: Annotated[str|None,Header()] = None,
    db: Session = Depends(get_db)
):
    lang = accept_language[:2] if accept_language else "en"
    return ProductService.get_product(product_id, lang, db)


@router.post("/",status_code=status.HTTP_201_CREATED,response_model=ProductOut)
def create_product(
    data: ProductIn , 
    is_admin: bool = Depends(require_admin),
    accept_language: Annotated[str|None,Header()] = None,
    db: Session = Depends(get_db)):

    if not is_admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Admin privileges required")

    lang = accept_language[:2] if accept_language else "en"

    return ProductService.create_product(data, lang, db)


@router.post("/{product_id}/images", status_code = status.HTTP_201_CREATED)
async def upload_product_images(
    product_id : int,
    files: Annotated[List[UploadFile], File(...)],
    is_admin: bool = Depends(require_admin),
    db : Session = Depends(get_db)
):
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Admin privileges required")

    return await ProductService.upload_product_images(product_id, files, db)
        

@router.put("/{product_id}", status_code=status.HTTP_200_OK, response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductUpdate,
    is_admin: bool = Depends(require_admin),
    accept_language: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db)
):
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin privileges required")

    lang = accept_language[:2] if accept_language else "en"

    return ProductService.update_product(product_id, data, lang, db)


@router.delete("/{product_id}", status_code= status.HTTP_200_OK)
def delete_product(
    product_id: int,
    is_admin: bool = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if not is_admin:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail="Admin privileges required")
    return ProductService.delete_product(product_id, db)
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers.cart.cart_schema import AddItemRequest, UpdateItemRequest, CartResponse
from app.routers.cart import cart_service as service
from app.routers.cart.cart_service import resolve_lang

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=CartResponse)
def get_cart(
    accept_language: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lang = resolve_lang(accept_language)
    return service.get_cart(current_user.id, db, lang)


@router.post("/items", response_model=CartResponse)
def add_item(
    body: AddItemRequest,
    accept_language: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lang = resolve_lang(accept_language)
    return service.add_item(current_user.id, body.product_id, body.quantity, db, lang)


@router.patch("/items/{product_id}", response_model=CartResponse)
def update_item(
    product_id: int,
    body: UpdateItemRequest,
    accept_language: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lang = resolve_lang(accept_language)
    return service.update_item(current_user.id, product_id, body.quantity, db, lang)


@router.delete("/items/{product_id}", response_model=CartResponse)
def remove_item(
    product_id: int,
    accept_language: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lang = resolve_lang(accept_language)
    return service.remove_item(current_user.id, product_id, db, lang)


@router.delete("", status_code=200)
def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.clear_cart(current_user.id, db)
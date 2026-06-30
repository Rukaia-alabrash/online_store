from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.routers.cart.cart_schema import CartItemResponse, CartResponse

DEFAULT_LANG = "en"
SUPPORTED_LANGS = {"en", "ar"}


def resolve_lang(accept_language: str | None) -> str:
    if not accept_language:
        return DEFAULT_LANG
    lang = accept_language.strip().lower()
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def get_or_create_cart(user_id: int, db: Session) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def get_product_name(product: Product, lang: str) -> str:
    translation = next(
        (t for t in product.product_translations if t.lang_code == lang),
        None,
    )
    if not translation:
        translation = next(
            (t for t in product.product_translations if t.lang_code == DEFAULT_LANG),
            None,
        )
    return translation.name if translation else ""


def get_product_image(product: Product) -> str:
    primary = next((img for img in product.images if img.is_primary), None)
    if primary:
        return primary.url
    if product.images:
        return product.images[0].url
    return ""


def build_cart_response(cart: Cart, db: Session, lang: str) -> CartResponse:
    items = []
    total = 0.0

    for item in cart.cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            items.append(CartItemResponse(
                product_id=product.id,
                name=get_product_name(product, lang),
                price=product.price,
                image=get_product_image(product),
                quantity=item.quantity,
            ))
            total += product.price * item.quantity

    return CartResponse(items=items, total=round(total, 2))


def get_cart(user_id: int, db: Session, lang: str) -> CartResponse:
    cart = get_or_create_cart(user_id, db)
    return build_cart_response(cart, db, lang)


def add_item(user_id: int, product_id: int, quantity: int, db: Session, lang: str) -> CartResponse:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    cart = get_or_create_cart(user_id, db)

    existing = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == product_id,
    ).first()

    if existing:
        existing.quantity += quantity
    else:
        db.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity))

    db.commit()
    db.refresh(cart)
    return build_cart_response(cart, db, lang)


def update_item(user_id: int, product_id: int, quantity: int, db: Session, lang: str) -> CartResponse:
    if quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    cart = get_or_create_cart(user_id, db)

    item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == product_id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    item.quantity = quantity
    db.commit()
    db.refresh(cart)
    return build_cart_response(cart, db, lang)


def remove_item(user_id: int, product_id: int, db: Session, lang: str) -> CartResponse:
    cart = get_or_create_cart(user_id, db)

    item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == product_id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    db.delete(item)
    db.commit()
    db.refresh(cart)
    return build_cart_response(cart, db, lang)


def clear_cart(user_id: int, db: Session) -> dict:
    cart = get_or_create_cart(user_id, db)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    return {"message": "Cart cleared"}
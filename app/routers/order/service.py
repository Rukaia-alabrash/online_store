import datetime
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.product import Product
from app.models.receipt import Receipt, ReceiptStatus
from app.models.order_item import OrderItem
from app.models.shipping_address import ShippingAddress

from app.routers.order.schema import (
    OrderCreate, OrderOut, OrderItemOut, ShippingAddressOut, UserItemOut,
)


class OrderReader:
    def __init__(self, db: Session):
        self.db = db

    def list_orders(
        self,
        page: int = 1,
        limit: int = 10,
        user_id: Optional[int] = None,
        status: Optional[ReceiptStatus] = None,
    ):
        query = self.db.query(Receipt).options(
            joinedload(Receipt.order_items),
            joinedload(Receipt.shipping_address),
        )

        if user_id is not None:
            query = query.filter(Receipt.user_id == user_id)
        if status is not None:
            query = query.filter(Receipt.status == status)

        total = query.count()
        offset = (page - 1) * limit
        orders = query.order_by(Receipt.id.desc()).offset(offset).limit(limit).all()
        return orders, total

    def to_order_out(self, receipt: Receipt) -> OrderOut:
        items_out = [
            OrderItemOut(id=str(oi.product_id), price=oi.price, quantity=oi.quantity)
            for oi in receipt.order_items
        ]

        shipping = receipt.shipping_address
        shipping_out = ShippingAddressOut(
            full_name=shipping.full_name,
            email=shipping.email,
            address=shipping.address,
            city=shipping.city,
            zip_code=shipping.zip_code,
        )

        return OrderOut(
            id=str(receipt.id),
            user_id=str(receipt.user_id),
            items=items_out,
            total=float(receipt.total_price),
            status=receipt.status.value if hasattr(receipt.status, "value") else receipt.status,
            shipping_address=shipping_out,
        )

    def get_orders_by_user_id(self, user_id: int):
        return (
            self.db.query(Receipt)
            .options(
                joinedload(Receipt.order_items)
                .joinedload(OrderItem.product)
                .joinedload(Product.product_translations),
                joinedload(Receipt.order_items)
                .joinedload(OrderItem.product)
                .joinedload(Product.images),
            )
            .filter(Receipt.user_id == user_id)
            .order_by(Receipt.id.desc())
            .all()
        )

    def user_order_items_out(self, receipts: list[Receipt], lang: str = "en") -> list[UserItemOut]:
        items_out = []

        for receipt in receipts:
            for oi in receipt.order_items:
                product = oi.product
                if not product:
                    continue

                translation = next(
                    (t for t in product.product_translations if t.lang_code == lang),
                    None,
                )
                if not translation:
                    translation = next(iter(product.product_translations), None)
                name = translation.name if translation else ""

                image = None
                if product.images:
                    primary = next((img.url for img in product.images if img.is_primary), None)
                    image = primary or product.images[0].url

                discount = None
                if product.discount_percentage and product.discount_percentage > 0:
                    if not product.discount_expiry or product.discount_expiry >= datetime.now(timezone.utc):
                        discount = product.discount_percentage

                items_out.append(UserItemOut(
                    id=str(oi.product_id),
                    name=name,
                    price=oi.price,
                    image=image,
                    rating=product.average_rating,
                    discount_percentage=discount,
                    quantity=oi.quantity,
                ))

        return items_out
    

class OrderWriter:
    TOTAL_TOLERANCE = 0.01

    def __init__(self, db: Session):
        self.db = db

    def _validate_total(self, order_data: OrderCreate) -> None:
        subtotal = sum(item.price * item.quantity for item in order_data.items)
        shipping = 0 if subtotal > 100 else 10
        tax = subtotal * 0.08
        expected_total = subtotal + shipping + tax

        if abs(expected_total - order_data.total) > self.TOTAL_TOLERANCE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Total mismatch: submitted total ({order_data.total}) does not "
                    f"match expected total ({expected_total:.2f})"
                ),
            )

    def create_order(self, order_data: OrderCreate) -> Receipt:
        self._validate_total(order_data)

        shipping_address = ShippingAddress(
            user_id=int(order_data.user_id),
            full_name=order_data.shipping_address.full_name,
            address=order_data.shipping_address.address,
            city=order_data.shipping_address.city,
            zip_code=order_data.shipping_address.zip_code,
        )
        self.db.add(shipping_address)
        self.db.flush()

        receipt = Receipt(
            user_id=int(order_data.user_id),
            shipping_address_id=shipping_address.id,
            total_price=order_data.total,
            payment_status="pending",
            status=ReceiptStatus.PENDING,
        )
        self.db.add(receipt)
        self.db.flush()

        for item in order_data.items:
            self.db.add(OrderItem(
                receipt_id=receipt.id,
                product_id=int(item.id),
                price=item.price,
                quantity=item.quantity,
            ))

        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def update_status(self, order_id: int, new_status: ReceiptStatus) -> Optional[Receipt]:
        receipt = self.db.query(Receipt).filter(Receipt.id == order_id).first()
        if receipt is None:
            return None
        receipt.status = new_status.value
        self.db.commit()
        self.db.refresh(receipt)
        return receipt
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.receipt import Receipt, ReceiptStatus
from app.models.order_item import OrderItem
from app.models.shipping_address import ShippingAddress

from app.routers.order.schema import OrderCreate, OrderOut, OrderItemOut, ShippingAddressOut


class OrderReader:
    """Handles all read/query operations for orders (GET /orders)."""

    def __init__(self, db: Session):
        self.db = db

    def list_orders(
        self,
        page: int = 1,
        limit: int = 10,
        user_id: Optional[int] = None,
        status: Optional[ReceiptStatus] = None,
    ):
        query = (
            self.db.query(Receipt)
            .options(
                joinedload(Receipt.order_items),
                joinedload(Receipt.shipping_address),
            )
        )

        if user_id is not None:
            query = query.filter(Receipt.user_id == user_id)

        if status is not None:
            query = query.filter(Receipt.status == status)

        total = query.count()

        offset = (page - 1) * limit
        orders = (
            query.order_by(Receipt.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return orders, total

    def to_order_out(self, receipt: Receipt, lang: str = "en") -> OrderOut:
        """
        Builds an OrderOut manually instead of relying on automatic
        from_attributes conversion, because Receipt's column names
        (user_id, total_price, etc.) don't match OrderOut's camelCase
        field names.

        Note: OrderItemOut no longer includes name/image -- the frontend
        team confirmed it doesn't need them in the response either.
        """
        items_out = [
            OrderItemOut(
                id=str(order_item.product_id),
                price=order_item.price,
                quantity=order_item.quantity,
            )
            for order_item in receipt.order_items
        ]

        shipping = receipt.shipping_address
        shipping_out = ShippingAddressOut(
            full_name=shipping.full_name,
            address=shipping.address,
            city=shipping.city,
            zip_code=shipping.zip_code,
        )

        return OrderOut(
            id=str(receipt.id),
            user_id=str(receipt.user_id),
            items=items_out,
            total=float(receipt.total_price),
            status=receipt.status.value,
            shipping_address=shipping_out,
            created_at=receipt.created_at,
            updated_at=getattr(receipt, "updated_at", None),
        )


class OrderWriter:
    """Handles all write operations for orders (POST /orders, PATCH /orders/:id/status)."""

    # allowed margin for float rounding differences (e.g. 334.789999 vs 334.79)
    TOTAL_TOLERANCE = 0.01

    def __init__(self, db: Session):
        self.db = db

    def _validate_total(self, order_data: OrderCreate) -> None:
        # Price calculation rules mirrored from api-contract.md section 7:
        #   subtotal = sum(item.price * item.quantity)
        #   shipping = 0 if subtotal > 100 else 10
        #   tax      = subtotal * 0.08
        #   total    = subtotal + shipping + tax
        subtotal = sum(item.price * item.quantity for item in order_data.items)
        shipping = 0 if subtotal > 100 else 10
        tax = subtotal * 0.08
        expected_total = subtotal + shipping + tax

        if abs(expected_total - order_data.total) > self.TOTAL_TOLERANCE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Total mismatch: submitted total ({order_data.total}) does not "
                    f"match expected total ({expected_total:.2f}) computed from "
                    f"items + shipping + tax"
                ),
            )

    def create_order(self, order_data: OrderCreate, lang: str = "en") -> Receipt:
        self._validate_total(order_data)

        shipping_address = ShippingAddress(
            user_id=int(order_data.user_id),
            full_name=order_data.shipping_address.full_name,
            address=order_data.shipping_address.address,
            city=order_data.shipping_address.city,
            zip_code=order_data.shipping_address.zip_code,
        )
        self.db.add(shipping_address)
        self.db.flush()  # get shipping_address.id without committing yet

        receipt = Receipt(
            user_id=int(order_data.user_id),
            shipping_address_id=shipping_address.id,
            total_price=order_data.total,
            payment_status="pending",
            status=ReceiptStatus.PENDING,
        )
        self.db.add(receipt)
        self.db.flush()  # get receipt.id

        for item in order_data.items:
            order_item = OrderItem(
                receipt_id=receipt.id,
                product_id=int(item.id),
                price=item.price,
                quantity=item.quantity,
            )
            self.db.add(order_item)

        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def update_status(self, order_id: int, new_status: ReceiptStatus) -> Optional[Receipt]:
        receipt = self.db.query(Receipt).filter(Receipt.id == order_id).first()
        if receipt is None:
            return None

        receipt.status = new_status
        self.db.commit()
        self.db.refresh(receipt)
        return receipt
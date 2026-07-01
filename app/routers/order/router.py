from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.receipt import ReceiptStatus

from app.routers.order.schema import (
    OrderOut, OrderCreate, UpdateOrderStatusBody, PaginatedOrders, UserItemOut,
)
from app.routers.order.service import OrderReader, OrderWriter
from app.routers.shared.pagination import Pagination


router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/myOrders", response_model=List[UserItemOut])
def get_my_orders(
    accept_language: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lang = accept_language[:2] if accept_language else "en"

    reader = OrderReader(db)
    receipts = reader.get_orders_by_user_id(current_user.id)

    if not receipts:
        raise HTTPException(status_code=404, detail="No orders found")

    return reader.user_order_items_out(receipts, lang)


@router.get("", response_model=PaginatedOrders)
def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    userId: Optional[str] = Query(None),
    order_status: Optional[ReceiptStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_admin = current_user.role.value.lower() == "admin"
    filter_user_id = (int(userId) if userId is not None else None) if is_admin else current_user.id

    reader = OrderReader(db)
    orders, total = reader.list_orders(
        page=page, limit=limit, user_id=filter_user_id, status=order_status,
    )

    return PaginatedOrders(
        orders=[reader.to_order_out(o) for o in orders],
        pagination=Pagination(
            page=page, limit=limit, total=total,
            totalPages=(total + limit - 1) // limit if limit else 0,
        ),
    )


# @router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
# def create_order(
#     order_data: OrderCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     if str(current_user.id) != order_data.user_id:
#         raise HTTPException(status_code=403, detail="Cannot create an order on behalf of another user")

#     writer = OrderWriter(db)
#     receipt = writer.create_order(order_data)

#     reader = OrderReader(db)
#     return reader.to_order_out(receipt)


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    body: UpdateOrderStatusBody,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin),
):
    writer = OrderWriter(db)
    receipt = writer.update_status(order_id, body.status)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Order not found")

    reader = OrderReader(db)
    return reader.to_order_out(receipt)
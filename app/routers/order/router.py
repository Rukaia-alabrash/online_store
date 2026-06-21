from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin, get_language
from app.models.user import User
from app.models.receipt import ReceiptStatus

from app.routers.order.schema import (
    OrderOut,
    OrderCreate,
    UpdateOrderStatusBody,
    PaginatedOrders,
)
from app.routers.order.service import OrderReader, OrderWriter
from app.routers.shared.pagination import Pagination


router = APIRouter(prefix="/orders", tags=["orders"])


# ---------- GET /orders ----------

@router.get("", response_model=PaginatedOrders)
def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    user_id: Optional[str] = Query(None),
    order_status: Optional[ReceiptStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_language),
):
    # Role: "any" per contract -- but a non-admin can only ever see their
    # own orders, regardless of what userId they pass in the query string.
    is_admin = current_user.role.value.lower() == "admin"

    if is_admin:
        filter_user_id = int(user_id) if user_id is not None else None
    else:
        filter_user_id = current_user.id

    reader = OrderReader(db)
    orders, total = reader.list_orders(
        page=page,
        limit=limit,
        user_id=filter_user_id,
        status=order_status,
    )

    return PaginatedOrders(
        orders=[reader.to_order_out(order, lang=lang) for order in orders],
        pagination=Pagination(
            page=page,
            limit=limit,
            total=total,
            totalPages=(total + limit - 1) // limit if limit else 0,
        ),
    )


# ---------- POST /orders ----------

@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_language),
):
    # Role: "user" per contract. A user can only create an order for themselves.
    if str(current_user.id) != order_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create an order on behalf of another user",
        )

    writer = OrderWriter(db)
    receipt = writer.create_order(order_data, lang=lang)

    reader = OrderReader(db)
    return reader.to_order_out(receipt, lang=lang)


# ---------- PATCH /orders/:id/status ----------

@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    body: UpdateOrderStatusBody,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin),
    lang: str = Depends(get_language),
):
    writer = OrderWriter(db)
    receipt = writer.update_status(order_id, body.status)

    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    reader = OrderReader(db)
    return reader.to_order_out(receipt, lang=lang)
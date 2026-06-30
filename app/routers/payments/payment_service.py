import os
import stripe
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.payment import Payment, PaymentIntentStatus
from app.models.receipt import Receipt, ReceiptStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.shipping_address import ShippingAddress
from app.models.user import User
from app.routers.payments.payment_schema import CreatePaymentIntentRequest

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class PaymentService:

    
    @staticmethod
    def create_payment_intent(
        payload: CreatePaymentIntentRequest,
        current_user: User,
        db: Session,
    ):
        shipping_address = (
            db.query(ShippingAddress)
            .filter(
                ShippingAddress.user_id == current_user.id,
                ShippingAddress.full_name == payload.shippingAddress.fullName,
                ShippingAddress.address == payload.shippingAddress.address,
                ShippingAddress.city == payload.shippingAddress.city,
                ShippingAddress.zip_code == payload.shippingAddress.zipCode,
            )
            .first()
        )
        if not shipping_address:
            shipping_address = ShippingAddress(
                user_id=current_user.id,
                full_name=payload.shippingAddress.fullName,
                address=payload.shippingAddress.address,
                city=payload.shippingAddress.city,
                zip_code=payload.shippingAddress.zipCode,
            )
            db.add(shipping_address)
            db.flush()

        # 2. Soft stock check — fast feedback before hitting Stripe
        for item in payload.items:
            product = (
                db.query(Product).filter(Product.id == item.productId).first()
            )
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {item.productId} not found",
                )
            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient stock for product {item.productId}",
                )

        # 3. Create Receipt (PENDING)
        receipt = Receipt(
            user_id=current_user.id,
            shipping_address_id=shipping_address.id,
            total_price=payload.amount,
            payment_status="pending",
            status=ReceiptStatus.PENDING,
        )
        db.add(receipt)
        db.flush()  # get receipt.id without committing

        # 4. Create OrderItems
        for item in payload.items:
            order_item = OrderItem(
                receipt_id=receipt.id,
                product_id=item.productId,
                price=item.price,
                quantity=item.quantity,
            )
            db.add(order_item)

        # 5. Call Stripe
        try:
            intent = stripe.PaymentIntent.create(
                amount=payload.amount,
                currency=payload.currency,
                payment_method=payload.paymentMethodId,
                confirm=False,
                metadata={
                    "user_id": current_user.id,
                    "receipt_id": receipt.id,
                },
            )
        except stripe.error.CardError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e.user_message),
            )
        except stripe.error.StripeError as e:
            db.rollback()
            print(f"Stripe error: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Payment processing error, please try again",
            )

        # 6. Create Payment record
        payment = Payment(
            user_id=current_user.id,
            receipt_id=receipt.id,
            amount=payload.amount,
            currency=payload.currency,
            status=PaymentIntentStatus.REQUIRES_CONFIRMATION,
            payment_method=payload.paymentMethodId,
            transaction_id=intent.id,
        )
        db.add(payment)
        db.commit()

        return {
            "clientSecret": intent.client_secret,
            "paymentIntentId": intent.id,
            "receiptId": receipt.id,
        }

    # ------------------------------------------------------------------ #
    #  REDUCE STOCK — called from webhook only                            #
    # ------------------------------------------------------------------ #
    @staticmethod
    def reduce_stock_for_receipt(receipt_id: int, db: Session):
        # Lock the receipt row
        receipt = (
            db.execute(
                select(Receipt)
                .where(Receipt.id == receipt_id)
                .with_for_update()
            )
            .scalar_one_or_none()
        )

        if not receipt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found",
            )

        # Idempotency guard — webhook can fire more than once
        if receipt.status != ReceiptStatus.PENDING:
            return

        # Lock each product and reduce stock
        for item in receipt.order_items:
            product = (
                db.execute(
                    select(Product)
                    .where(Product.id == item.product_id)
                    .with_for_update()
                )
                .scalar_one_or_none()
            )

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {item.product_id} not found",
                )

            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient stock for product {product.id}",
                )

            product.stock -= item.quantity

        # Mark receipt as confirmed
        receipt.status = ReceiptStatus.CONFIRMED
        receipt.payment_status = "paid"
        db.commit()


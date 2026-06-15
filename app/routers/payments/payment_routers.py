import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.payment import Payment, PaymentIntentStatus
from app.models.receipt import Receipt, ReceiptStatus
from app.routers.payments.payment_schema import CreatePaymentIntentRequest, CreatePaymentIntentResponse
from app.routers.payments.payment_service import PaymentService
from app.routers.payments.payment_schema import ReceiptOut

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(prefix="/payments", tags=["payments"])


#  POST /payments/create-intent                                        
@router.post(
    "/create-intent",
    response_model=CreatePaymentIntentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_intent(
    payload: CreatePaymentIntentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PaymentService.create_payment_intent(payload, current_user, db)



#  POST /payments/webhook  — Stripe calls this after payment   
@router.post("/webhook/")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured",
        )

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature header",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )

    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe signature",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook error: {str(e)}",
        )


    # ── Payment succeeded ──────────────────────────────────────────
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]

        payment = (
            db.query(Payment)
            .filter(Payment.transaction_id == intent["id"])
            .first()
        )
        
        if payment:
            payment.status = PaymentIntentStatus.SUCCEEDED
            db.commit()

            try:
                PaymentService.reduce_stock_for_receipt(
                    payment.receipt_id, db
                )
            except HTTPException:
                # Stock ran out between soft check and now — refund
                stripe.Refund.create(payment_intent=intent["id"])
                payment.status = PaymentIntentStatus.CANCELED
                receipt = db.query(Receipt).filter(
                    Receipt.id == payment.receipt_id
                ).first()
                if receipt:
                    receipt.status = ReceiptStatus.CANCELLED
                    receipt.payment_status = "refunded"
                db.commit()

    # ── Payment failed ─────────────────────────────────────────────
    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]

        payment = (
            db.query(Payment)
            .filter(Payment.transaction_id == intent["id"])
            .first()
        )
        if payment:
            payment.status = PaymentIntentStatus.CANCELED
            receipt = db.query(Receipt).filter(
                Receipt.id == payment.receipt_id
            ).first()
            if receipt:
                receipt.status = ReceiptStatus.CANCELLED
                receipt.payment_status = "failed"
            db.commit()

    return {"received": True}
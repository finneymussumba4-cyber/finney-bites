from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.order import OrderCreate, OrderResponse
from app.services.orders import create_order
from app.security import get_optional_current_user
from app.models import User

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=201)
def place_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user)
):
    if user and user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer account required")

    try:
        order = create_order(db, data, user_id=user.id if user else None)
        return order

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process your order. Please try again."
        )

from sqlalchemy.exc import IntegrityError
from app.models import DeliveryZone, Order
from app.schemas.payment import PaymentReferenceSubmit


def normalize_phone(phone: str) -> str:
    digits = "".join(character for character in phone if character.isdigit())

    if digits.startswith("0"):
        return "254" + digits[1:]

    if digits.startswith("254"):
        return digits

    return digits


@router.post("/{order_number}/payment-reference")
def submit_payment_reference(
    order_number: str,
    data: PaymentReferenceSubmit,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(
        Order.order_number == order_number
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if normalize_phone(data.customer_phone) != normalize_phone(order.customer_phone):
        raise HTTPException(status_code=403, detail="Phone number does not match this order")

    if order.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cancelled orders cannot receive payments")

    if order.payment_status == "paid":
        raise HTTPException(status_code=400, detail="This order is already paid")

    reference = data.mpesa_reference.strip().upper()

    existing = db.query(Order).filter(
        Order.mpesa_reference == reference,
        Order.id != order.id
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="This M-Pesa reference has already been submitted")

    order.mpesa_reference = reference
    order.payment_status = "unverified"

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This M-Pesa reference has already been used")

    return {
        "message": "Payment reference submitted successfully. Awaiting administrator verification.",
        "order_number": order.order_number,
        "payment_status": order.payment_status
    }
from io import BytesIO
from fastapi import Query
from fastapi.responses import StreamingResponse
from app.services.receipts import generate_receipt


@router.get("/{order_number}/receipt")
def download_order_receipt(
    order_number: str,
    customer_phone: str = Query(min_length=9, max_length=20),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(
        Order.order_number == order_number
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if normalize_phone(customer_phone) != normalize_phone(order.customer_phone):
        raise HTTPException(
            status_code=403,
            detail="Phone number does not match this order"
        )

    try:
        pdf = generate_receipt(order)

        return StreamingResponse(
            BytesIO(pdf),
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{order.order_number}.pdf"'
                )
            }
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to generate receipt"
        )
from app.services.whatsapp_receipts import send_order_receipt_via_whatsapp


@router.post("/{order_number}/whatsapp-receipt")
def request_whatsapp_receipt(
    order_number: str,
    customer_phone: str = Query(min_length=9, max_length=20),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(
        Order.order_number == order_number
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if normalize_phone(customer_phone) != normalize_phone(order.customer_phone):
        raise HTTPException(
            status_code=403,
            detail="Phone number does not match this order"
        )

    try:
        result = send_order_receipt_via_whatsapp(order)

        if not result.get("success"):
            raise HTTPException(
                status_code=503,
                detail=result
            )

        return result

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to send WhatsApp receipt"
        )



@router.get("/delivery-zones")
def get_delivery_zones(db: Session = Depends(get_db)):
    zones = db.query(DeliveryZone).filter(
        DeliveryZone.is_active == True
    ).order_by(DeliveryZone.name).all()

    return [
        {
            "id": zone.id,
            "name": zone.name,
            "delivery_fee": float(zone.delivery_fee)
        }
        for zone in zones
    ]



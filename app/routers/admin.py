from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Product, Category, User
from app.security import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])


@router.get("/dashboard")
def admin_dashboard(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    total_revenue = db.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(Order.payment_status == "paid").scalar()

    pending_payments = db.query(Order).filter(
        Order.payment_status != "paid",
        Order.status != "cancelled"
    ).count()

    return {
        "message": "Welcome to FINNEY BITES Admin Dashboard",
        "administrator": admin.full_name,
        "statistics": {
            "total_products": db.query(Product).count(),
            "total_categories": db.query(Category).count(),
            "total_users": db.query(User).count(),
            "total_customers": db.query(User).filter(User.role == "customer").count(),
            "total_orders": db.query(Order).count(),
            "total_revenue": float(total_revenue or 0),
            "pending_payments": pending_payments
        }
    }

from fastapi import HTTPException
from sqlalchemy import update
from app.models import Order, OrderItem, InventoryLog, CustomerLoyalty


@router.post("/orders/{order_number}/confirm")
def confirm_order(
    order_number: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        order = db.query(Order).filter(
            Order.order_number == order_number
        ).first()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.stock_deducted:
            return {
                "message": "Order was already confirmed. Stock was not deducted again.",
                "order_number": order.order_number
            }

        if order.status == "cancelled":
            raise HTTPException(status_code=400, detail="Cancelled orders cannot be confirmed")

        for item in order.items:
            result = db.execute(
                update(Product)
                .where(
                    Product.id == item.product_id,
                    Product.stock_quantity >= item.quantity
                )
                .values(
                    stock_quantity=Product.stock_quantity - item.quantity
                )
            )

            if result.rowcount != 1:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {item.product_name}"
                )

            db.add(InventoryLog(
                product_id=item.product_id,
                change_quantity=-item.quantity,
                reason=f"Order {order.order_number} confirmed"
            ))

        order.stock_deducted = True
        order.status = "confirmed"

        db.commit()

        return {
            "message": "Order confirmed and stock deducted successfully",
            "order_number": order.order_number,
            "status": order.status,
            "stock_deducted": order.stock_deducted
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to confirm order"
        )

from decimal import Decimal
from app.schemas.payment import PaymentVerification


@router.post("/orders/{order_number}/verify-payment")
def verify_order_payment(
    order_number: str,
    data: PaymentVerification,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(
        Order.order_number == order_number
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cancelled orders cannot be paid")

    if order.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Payment is already verified")

    if not order.mpesa_reference:
        raise HTTPException(status_code=400, detail="Customer has not submitted an M-Pesa reference")

    if data.mpesa_reference.strip().upper() != order.mpesa_reference:
        raise HTTPException(status_code=400, detail="M-Pesa reference does not match")

    if not data.confirmed_in_statement:
        raise HTTPException(status_code=400, detail="Confirm the transaction in the M-Pesa statement first")

    received_amount = Decimal(str(data.received_amount)).quantize(Decimal("0.01"))

    if received_amount != order.total_amount:
        raise HTTPException(status_code=400, detail="Received amount does not match the order total")

    order.payment_status = "paid"

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to verify payment")

    return {
        "message": "Payment successfully verified",
        "order_number": order.order_number,
        "payment_status": order.payment_status,
        "verified_by": admin.full_name
    }
from app.models import Review


@router.get("/reviews/pending")
def get_pending_reviews(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    reviews = db.query(Review).filter(
        Review.is_approved == False
    ).order_by(Review.created_at.desc()).all()

    return [
        {
            "id": review.id,
            "order_id": review.order_id,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at
        }
        for review in reviews
    ]


@router.post("/reviews/{review_id}/approve")
def approve_review(
    review_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    review = db.query(Review).filter(
        Review.id == review_id
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.is_approved:
        return {"message": "Review is already approved"}

    review.is_approved = True
    db.commit()

    return {
        "message": "Review approved successfully",
        "review_id": review.id,
        "approved": True
    }
@router.post("/orders/{order_number}/complete")
def complete_order(
    order_number: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(
        Order.order_number == order_number
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cancelled orders cannot be completed")

    if order.status == "completed":
        return {"message": "Order is already completed"}

    if order.payment_status != "paid":
        raise HTTPException(status_code=400, detail="Payment must be verified first")

    if not order.stock_deducted or order.status != "confirmed":
        raise HTTPException(status_code=400, detail="Order must be confirmed first")

    points_awarded = 0
    loyalty_message = "Guest orders do not earn loyalty points."

    if order.user_id:
        loyalty = db.query(CustomerLoyalty).filter(
            CustomerLoyalty.user_id == order.user_id
        ).first()

        if not loyalty:
            existing_phone_record = db.query(CustomerLoyalty).filter(
                CustomerLoyalty.customer_phone == order.customer_phone
            ).first()

            if existing_phone_record:
                loyalty_message = (
                    "Loyalty points not added because this phone has "
                    "an existing unlinked loyalty record."
                )
            else:
                loyalty = CustomerLoyalty(
                    user_id=order.user_id,
                    customer_phone=order.customer_phone,
                    completed_orders=0,
                    points_balance=0,
                    lifetime_points=0
                )
                db.add(loyalty)
                db.flush()

        if loyalty:
            loyalty.completed_orders += 1

            if loyalty.completed_orders % 6 == 0:
                points_awarded = 150
                loyalty.points_balance += points_awarded
                loyalty.lifetime_points += points_awarded

            loyalty_message = (
                f"{points_awarded} loyalty points awarded."
                if points_awarded
                else f"{6 - (loyalty.completed_orders % 6)} more completed orders until the next reward."
            )

    order.status = "completed"
    db.commit()

    return {
        "message": "Order completed successfully",
        "order_number": order.order_number,
        "status": order.status,
        "completed_by": admin.full_name,
        "points_awarded": points_awarded,
        "loyalty_message": loyalty_message
    }
from app.services.whatsapp import whatsapp_status

@router.get("/whatsapp-status")
def get_whatsapp_status(
    admin: User = Depends(get_current_admin)
):
    return whatsapp_status()


from fastapi import Query


@router.get("/orders")
def get_all_orders(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    orders = db.query(Order).order_by(
        Order.created_at.desc()
    ).offset(offset).limit(limit).all()

    return [
        {
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "mpesa_reference": order.mpesa_reference,
            "order_type": order.order_type,
            "items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "line_total": float(item.line_total)
                }
                for item in order.items
            ],
            "total_amount": float(order.total_amount),
            "payment_status": order.payment_status,
            "status": order.status,
            "created_at": order.created_at
        }
        for order in orders
    ]

from app.models import ContactMessage


@router.get("/messages")
def get_customer_messages(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    messages = db.query(ContactMessage).order_by(
        ContactMessage.created_at.desc()
    ).all()

    return [
        {
            "id": message.id,
            "name": message.name,
            "email": message.email,
            "phone": message.phone,
            "subject": message.subject,
            "message": message.message,
            "status": message.status,
            "created_at": message.created_at
        }
        for message in messages
    ]
@router.patch("/messages/{message_id}/status")
def update_message_status(
    message_id: int,
    status: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    allowed_statuses = ["new", "read", "resolved"]

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid message status"
        )

    message = db.query(ContactMessage).filter(
        ContactMessage.id == message_id
    ).first()

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Message not found"
        )

    message.status = status
    db.commit()

    return {
        "message": "Customer message status updated",
        "message_id": message.id,
        "status": message.status
    }
from app.schemas.product import ProductCreate


@router.post("/products", status_code=201)
def create_product(
    data: ProductCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(
        Category.id == data.category_id,
        Category.is_active == True
    ).first()

    if not category:
        raise HTTPException(
            status_code=400,
            detail="Invalid or inactive product category"
        )

    product = Product(**data.model_dump())

    try:
        db.add(product)
        db.commit()
        db.refresh(product)

        return {
            "message": "Product created successfully",
            "product_id": product.id,
            "name": product.name,
            "price": str(product.price)
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to create product"
        )

from app.schemas.product import ProductUpdate


@router.patch("/products/{product_id}")
def update_product(
    product_id: int,
    data: ProductUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    updates = data.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    if "category_id" in updates:
        category = db.query(Category).filter(
            Category.id == updates["category_id"],
            Category.is_active == True
        ).first()

        if not category:
            raise HTTPException(
                status_code=400,
                detail="Invalid or inactive category"
            )

    try:
        if "stock_quantity" in updates:
            difference = updates["stock_quantity"] - product.stock_quantity

            if difference != 0:
                db.add(InventoryLog(
                    product_id=product.id,
                    change_quantity=difference,
                    reason="Admin stock adjustment"
                ))

        for field, value in updates.items():
            setattr(product, field, value)

        db.commit()
        db.refresh(product)

        return {
            "message": "Product updated successfully",
            "product_id": product.id,
            "name": product.name,
            "price": str(product.price),
            "stock_quantity": product.stock_quantity
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to update product"
        )

@router.get("/products")
def list_admin_products(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    products = db.query(Product).order_by(Product.id.desc()).all()

    return {
        "total": len(products),
        "products": [
            {
                "id": product.id,
                "name": product.name,
                "category_id": product.category_id,
                "price": str(product.price),
                "stock_quantity": product.stock_quantity,
                "is_available": product.is_available,
                "is_featured": product.is_featured
            }
            for product in products
        ]
    }

@router.delete("/products/{product_id}")
def deactivate_product(
    product_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_available = False

    try:
        db.commit()
        return {
            "message": "Product deactivated successfully",
            "product_id": product.id
        }
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to deactivate product"
        )







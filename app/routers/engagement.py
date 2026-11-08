from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Review, NewsletterSubscriber, ContactMessage, Order
from app.schemas.engagement import (
    ReviewCreate,
    NewsletterSubscribe,
    ContactCreate
)

router = APIRouter(tags=["Customer Engagement"])


def normalize_phone(phone: str) -> str:
    digits = "".join(character for character in phone if character.isdigit())
    if digits.startswith("0"):
        return "254" + digits[1:]
    return digits


@router.get("/api/reviews/")
def get_approved_reviews(db: Session = Depends(get_db)):
    return db.query(Review).filter(
        Review.is_approved == True
    ).order_by(Review.created_at.desc()).all()


@router.post("/api/reviews/{order_number}")
def submit_review(
    order_number: str,
    data: ReviewCreate,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(
        Order.order_number == order_number
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if normalize_phone(data.customer_phone) != normalize_phone(order.customer_phone):
        raise HTTPException(status_code=403, detail="Phone number does not match this order")

    if order.status != "completed" or order.payment_status != "paid":
        raise HTTPException(
            status_code=400,
            detail="Only paid and completed orders can be reviewed"
        )

    existing = db.query(Review).filter(
        Review.order_id == order.id
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="This order already has a review")

    review = Review(
        order_id=order.id,
        rating=data.rating,
        comment=data.comment.strip(),
        is_approved=False
    )

    try:
        db.add(review)
        db.commit()
        return {"message": "Review submitted and awaiting approval"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This order already has a review")


@router.post("/api/newsletter/subscribe")
def subscribe_newsletter(
    data: NewsletterSubscribe,
    db: Session = Depends(get_db)
):
    email = str(data.email).lower()
    subscriber = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == email
    ).first()

    if subscriber:
        if subscriber.is_active:
            return {"message": "You are already subscribed"}
        subscriber.is_active = True
    else:
        db.add(NewsletterSubscriber(email=email, is_active=True))

    db.commit()
    return {"message": "Newsletter subscription successful"}


@router.post("/api/contact/")
def send_contact_message(
    data: ContactCreate,
    db: Session = Depends(get_db)
):
    contact = ContactMessage(
        name=data.name.strip(),
        email=str(data.email).lower(),
        phone=data.phone.strip() if data.phone else None,
        subject=data.subject.strip(),
        message=data.message.strip(),
        status="new"
    )

    db.add(contact)
    db.commit()

    return {"message": "Your message has been received successfully"}

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Order, Review

client = TestClient(app)
order_number = None
review_id = None

payload = {
    "customer_name": "Test Customer",
    "customer_phone": "0712345678",
    "order_type": "pickup",
    "items": [{"product_id": 1, "quantity": 1}]
}

try:
    order_response = client.post("/api/orders/", json=payload)
    print("ORDER:", order_response.status_code)

    if order_response.status_code != 201:
        print(order_response.json())
        raise RuntimeError("Test order creation failed")

    order_number = order_response.json()["order_number"]

    db = SessionLocal()
    try:
        order = db.query(Order).filter(
            Order.order_number == order_number
        ).first()

        order.status = "completed"
        order.payment_status = "paid"
        db.commit()
    finally:
        db.close()

    review_payload = {
        "customer_phone": "0712345678",
        "rating": 5,
        "comment": "Excellent food and service."
    }

    first = client.post(
        f"/api/reviews/{order_number}",
        json=review_payload
    )
    print("FIRST REVIEW:", first.status_code, first.json())

    public = client.get("/api/reviews/")
    print("PUBLIC REVIEWS:", public.status_code, public.json())

    duplicate = client.post(
        f"/api/reviews/{order_number}",
        json=review_payload
    )
    print("DUPLICATE REVIEW:", duplicate.status_code, duplicate.json())

finally:
    if order_number:
        db = SessionLocal()
        try:
            order = db.query(Order).filter(
                Order.order_number == order_number
            ).first()

            if order:
                db.query(Review).filter(
                    Review.order_id == order.id
                ).delete()
                db.delete(order)
                db.commit()

            print("TEST DATA CLEANED")
        finally:
            db.close()

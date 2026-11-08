import secrets
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Order

client = TestClient(app)
order_number = None

try:
    order_response = client.post(
        "/api/orders/",
        json={
            "customer_name": "Payment Test",
            "customer_phone": "0712345678",
            "order_type": "pickup",
            "items": [{"product_id": 1, "quantity": 1}]
        }
    )

    print("ORDER STATUS:", order_response.status_code)

    if order_response.status_code != 201:
        print(order_response.json())
        raise SystemExit("Order creation failed")

    order_number = order_response.json()["order_number"]

    reference = "TEST" + secrets.token_hex(5).upper()

    payment_response = client.post(
        f"/api/orders/{order_number}/payment-reference",
        json={
            "customer_phone": "254712345678",
            "mpesa_reference": reference
        }
    )

    print("PAYMENT STATUS:", payment_response.status_code)
    print("PAYMENT RESPONSE:", payment_response.json())

    if payment_response.status_code != 200:
        raise SystemExit("Payment reference test failed")

    print("EXPECTED PAYMENT STATUS: unverified")

finally:
    if order_number:
        db = SessionLocal()
        try:
            test_order = db.query(Order).filter(
                Order.order_number == order_number
            ).first()
            if test_order:
                db.delete(test_order)
                db.commit()
                print("TEST ORDER CLEANED UP: True")
        finally:
            db.close()

from getpass import getpass
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Order
import secrets

client = TestClient(app)
order_number = None

try:
    email = input("Administrator email: ")
    password = getpass("Administrator password: ")

    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": password}
    )

    print("LOGIN STATUS:", login.status_code)

    if login.status_code != 200:
        raise SystemExit("Administrator login failed")

    order_response = client.post(
        "/api/orders/",
        json={
            "customer_name": "Payment Verification Test",
            "customer_phone": "0712345678",
            "order_type": "pickup",
            "items": [{"product_id": 1, "quantity": 1}]
        }
    )

    print("ORDER STATUS:", order_response.status_code)

    if order_response.status_code != 201:
        print(order_response.json())
        raise SystemExit("Order creation failed")

    order_data = order_response.json()
    order_number = order_data["order_number"]
    reference = "TEST" + secrets.token_hex(5).upper()

    submission = client.post(
        f"/api/orders/{order_number}/payment-reference",
        json={
            "customer_phone": "0712345678",
            "mpesa_reference": reference
        }
    )

    print("REFERENCE SUBMISSION:", submission.status_code)

    verification = client.post(
        f"/api/admin/orders/{order_number}/verify-payment",
        json={
            "mpesa_reference": reference,
            "received_amount": order_data["total_amount"],
            "confirmed_in_statement": True
        }
    )

    print("VERIFICATION STATUS:", verification.status_code)
    print("VERIFICATION RESPONSE:", verification.json())

    if verification.status_code == 200:
        print("PAYMENT TEST: PASSED")
    else:
        print("PAYMENT TEST: FAILED")

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

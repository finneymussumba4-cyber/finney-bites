from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Order

client = TestClient(app)

payload = {
    "customer_name": "Test Customer",
    "customer_phone": "0712345678",
    "order_type": "pickup",
    "items": [{"product_id": 1, "quantity": 2}]
}

response = client.post("/api/orders/", json=payload)

print("STATUS:", response.status_code)
print("RESPONSE:", response.json())

if response.status_code == 201:
    order_number = response.json()["order_number"]
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

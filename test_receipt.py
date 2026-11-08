from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Order

client = TestClient(app)
order_number = None

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

    receipt = client.get(
        f"/api/orders/{order_number}/receipt",
        params={"customer_phone": "0712345678"}
    )

    print("RECEIPT STATUS:", receipt.status_code)
    print("CONTENT TYPE:", receipt.headers.get("content-type"))
    print("PDF SIGNATURE:", receipt.content[:5])
    print("PDF SIZE:", len(receipt.content), "bytes")

    assert receipt.status_code == 200
    assert receipt.headers.get("content-type") == "application/pdf"
    assert receipt.content.startswith(b"%PDF-")

    print("PDF GENERATION TEST: PASSED")

finally:
    if order_number:
        db = SessionLocal()
        try:
            order = db.query(Order).filter(
                Order.order_number == order_number
            ).first()

            if order:
                db.delete(order)
                db.commit()

            print("TEST ORDER CLEANED")
        finally:
            db.close()

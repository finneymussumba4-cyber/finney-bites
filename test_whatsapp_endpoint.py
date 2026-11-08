from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import Order, OrderItem, Product

client = TestClient(app)
db = SessionLocal()

order_number = "FB-WHATSAPP-TEST"

try:
    product = db.query(Product).first()

    if not product:
        raise RuntimeError("No test product found.")

    order = Order(
        order_number=order_number,
        customer_name="Test Customer",
        customer_phone="0700000000",
        order_type="pickup",
        subtotal=Decimal("500.00"),
        discount_amount=Decimal("0.00"),
        delivery_fee=Decimal("0.00"),
        total_amount=Decimal("500.00"),
        status="received",
        payment_status="unverified",
        stock_deducted=False
    )

    order.items.append(OrderItem(
        product_id=product.id,
        product_name=product.name,
        unit_price=Decimal("500.00"),
        quantity=1,
        line_total=Decimal("500.00")
    ))

    db.add(order)
    db.commit()

    print("TEST 1: Incorrect phone number")

    response = client.post(
        f"/api/orders/{order_number}/whatsapp-receipt",
        params={"customer_phone": "0799999999"}
    )

    print("Status:", response.status_code)
    assert response.status_code == 403

    print("PASSED: Incorrect phone rejected.")

    print("\nTEST 2: Correct phone, missing WhatsApp credentials")

    response = client.post(
        f"/api/orders/{order_number}/whatsapp-receipt",
        params={"customer_phone": "0700000000"}
    )

    print("Status:", response.status_code)
    print("Response:", response.json())

    assert response.status_code == 503
    assert response.json()["detail"]["stage"] == "upload"

    print("PASSED: Dry-run correctly prevented sending.")

finally:
    test_order = db.query(Order).filter(
        Order.order_number == order_number
    ).first()

    if test_order:
        db.delete(test_order)
        db.commit()

    db.close()

print("\nTEST ORDER CLEANED")
print("ALL TESTS PASSED")

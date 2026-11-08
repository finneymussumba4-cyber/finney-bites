from types import SimpleNamespace
from decimal import Decimal
from app.services.whatsapp_receipts import send_order_receipt_via_whatsapp

item = SimpleNamespace(
    product_name="Test Burger",
    quantity=2,
    unit_price=Decimal("500.00"),
    line_total=Decimal("1000.00")
)

order = SimpleNamespace(
    order_number="FB-TEST-001",
    customer_name="Test Customer",
    customer_phone="0769943592",
    order_type="pickup",
    status="received",
    payment_status="unverified",
    created_at="2026-11-05",
    items=[item],
    subtotal=Decimal("1000.00"),
    discount_amount=Decimal("0.00"),
    delivery_fee=Decimal("0.00"),
    total_amount=Decimal("1000.00")
)

result = send_order_receipt_via_whatsapp(order)

print("WORKFLOW RESULT:", result)

assert result["success"] is False
assert result["stage"] == "upload"

print("DRY-RUN WORKFLOW TEST: PASSED")

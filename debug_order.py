import traceback
from app.database import SessionLocal
from app.schemas.order import OrderCreate
from app.services.orders import create_order

db = SessionLocal()

try:
    data = OrderCreate(
        customer_name="Test Customer",
        customer_phone="0712345678",
        order_type="pickup",
        items=[{"product_id": 1, "quantity": 2}]
    )

    order = create_order(db, data)
    print("ORDER CREATED:", order.order_number)

except Exception:
    traceback.print_exc()

finally:
    db.close()

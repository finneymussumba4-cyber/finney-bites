from app.database import SessionLocal
from app.models import Order, Product, InventoryLog

ORDER_NUMBER = "FB-20261105-61A66D"

db = SessionLocal()

try:
    order = db.query(Order).filter(
        Order.order_number == ORDER_NUMBER
    ).first()

    if not order:
        print("Test order not found.")
    else:
        if order.stock_deducted:
            for item in order.items:
                product = db.query(Product).filter(
                    Product.id == item.product_id
                ).first()
                product.stock_quantity += item.quantity

        db.query(InventoryLog).filter(
            InventoryLog.reason == f"Order {ORDER_NUMBER} confirmed"
        ).delete(synchronize_session=False)

        db.delete(order)
        db.commit()
        print("TEST DATA CLEANED UP SUCCESSFULLY")

finally:
    db.close()

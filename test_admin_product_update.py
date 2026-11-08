from getpass import getpass
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import Category, Product, InventoryLog

client = TestClient(app)
db = SessionLocal()

test_name = "FINNEY UPDATE TEST"
product = None

try:
    category = db.query(Category).first()

    if not category:
        raise RuntimeError("No category found.")

    print("TEST 1: Administrator login")

    email = input("Admin email: ")
    password = getpass("Admin password: ")

    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": password}
    )

    print("Login status:", login.status_code)
    assert login.status_code == 200

    print("\nTEST 2: Create temporary product")

    product = Product(
        category_id=category.id,
        name=test_name,
        description="Temporary update test",
        price=100,
        stock_quantity=5,
        is_available=True,
        is_featured=False
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    product_id = product.id
    print("Product ID:", product_id)

    print("\nTEST 3: Update price and stock")

    response = client.patch(
        f"/api/admin/products/{product_id}",
        json={"price": "150.00", "stock_quantity": 10}
    )

    print("Status:", response.status_code)
    print("Response:", response.json())

    assert response.status_code == 200
    assert response.json()["price"] == "150.00"
    assert response.json()["stock_quantity"] == 10

    log = db.query(InventoryLog).filter(
        InventoryLog.product_id == product_id,
        InventoryLog.reason == "Admin stock adjustment"
    ).first()

    assert log is not None
    assert log.change_quantity == 5

    print("PASSED: Product updated and stock adjustment logged.")

finally:
    if product:
        db.query(InventoryLog).filter(
            InventoryLog.product_id == product.id
        ).delete(synchronize_session=False)

        db.delete(product)
        db.commit()

    db.close()

print("\nTEST DATA CLEANED")
print("ALL TESTS PASSED")

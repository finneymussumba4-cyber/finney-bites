from getpass import getpass
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import Category, Product

client = TestClient(app)
db = SessionLocal()
product = None

try:
    category = db.query(Category).first()

    product = Product(
        category_id=category.id,
        name="FINNEY DEACTIVATION TEST",
        price=100,
        stock_quantity=5,
        is_available=True,
        is_featured=False
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    product_id = product.id

    print("TEST 1: Unauthenticated access")

    response = client.delete(
        f"/api/admin/products/{product_id}"
    )

    print("Status:", response.status_code)
    assert response.status_code == 401

    print("PASSED: Unauthenticated access rejected.")

    print("\nTEST 2: Administrator login")

    email = input("Admin email: ")
    password = getpass("Admin password: ")

    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": password}
    )

    assert login.status_code == 200

    print("Login successful.")

    print("\nTEST 3: Deactivate product")

    response = client.delete(
        f"/api/admin/products/{product_id}"
    )

    print("Status:", response.status_code)
    print("Response:", response.json())

    assert response.status_code == 200

    db.refresh(product)
    assert product.is_available is False

    print("PASSED: Product successfully deactivated.")

finally:
    if product:
        db.delete(product)
        db.commit()

    db.close()

print("\nTEST DATA CLEANED")
print("ALL TESTS PASSED")

from getpass import getpass
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import Category, Product

client = TestClient(app)
db = SessionLocal()

test_name = "FINNEY TEST PRODUCT"

try:
    category = db.query(Category).first()

    if not category:
        raise RuntimeError("No product category found.")

    print("TEST 1: Unauthenticated product creation")

    payload = {
        "category_id": category.id,
        "name": test_name,
        "description": "Temporary test product",
        "price": "123.50",
        "stock_quantity": 5,
        "is_available": True,
        "is_featured": False
    }

    response = client.post("/api/admin/products", json=payload)

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

    print("Login status:", login.status_code)
    assert login.status_code == 200

    print("\nTEST 3: Create product")

    response = client.post("/api/admin/products", json=payload)

    print("Status:", response.status_code)
    print("Response:", response.json())

    assert response.status_code == 201
    assert response.json()["name"] == test_name

    print("PASSED: Product created successfully.")

finally:
    test_product = db.query(Product).filter(
        Product.name == test_name
    ).first()

    if test_product:
        db.delete(test_product)
        db.commit()

    db.close()

print("\nTEST PRODUCT CLEANED")
print("ALL TESTS PASSED")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("ADMIN LOGIN")
email = input("Enter administrator email: ")
from getpass import getpass
password = getpass("Enter administrator password: ")

login = client.post("/api/auth/login", json={
    "email": email,
    "password": password
})
print("LOGIN STATUS:", login.status_code)

if login.status_code != 200:
    print(login.json())
    raise SystemExit("Login failed")

order = client.post("/api/orders/", json={
    "customer_name": "Stock Test",
    "customer_phone": "0712345678",
    "order_type": "pickup",
    "items": [{"product_id": 1, "quantity": 2}]
})

print("ORDER STATUS:", order.status_code)

if order.status_code != 201:
    print(order.json())
    raise SystemExit("Test order creation failed")

order_number = order.json()["order_number"]
print("TEST ORDER:", order_number)

confirmation = client.post(
    f"/api/admin/orders/{order_number}/confirm"
)

print("CONFIRMATION STATUS:", confirmation.status_code)
print("CONFIRMATION RESPONSE:", confirmation.json())

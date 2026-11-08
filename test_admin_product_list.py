from getpass import getpass
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

print("TEST 1: Unauthenticated access")

response = client.get("/api/admin/products")

print("Status:", response.status_code)
assert response.status_code == 401

print("PASSED: Access rejected.")

print("\nTEST 2: Administrator login")

email = input("Admin email: ")
password = getpass("Admin password: ")

login = client.post(
    "/api/auth/login",
    json={"email": email, "password": password}
)

print("Login status:", login.status_code)
assert login.status_code == 200

print("\nTEST 3: Retrieve products")

response = client.get("/api/admin/products")

print("Status:", response.status_code)

data = response.json()

print("Total products:", data["total"])

assert response.status_code == 200
assert data["total"] >= 34

print("PASSED: Administrator can retrieve products.")
print("ALL TESTS PASSED")

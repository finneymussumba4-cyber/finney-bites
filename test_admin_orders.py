from getpass import getpass
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("TEST 1: Access without login")

response = client.get("/api/admin/orders")
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

print("\nTEST 3: Access orders as administrator")

response = client.get("/api/admin/orders")

print("Status:", response.status_code)
print("Orders returned:", len(response.json()))

assert response.status_code == 200
assert isinstance(response.json(), list)

print("\nALL TESTS PASSED")

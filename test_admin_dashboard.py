from getpass import getpass
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("TEST 1: Dashboard protection")
response = client.get("/api/admin/dashboard")
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
print("PASSED: Administrator login successful.")

print("\nTEST 3: Dashboard statistics")
response = client.get("/api/admin/dashboard")

assert response.status_code == 200

data = response.json()
statistics = data["statistics"]

for key, value in statistics.items():
    print(f"{key}: {value}")

required = [
    "total_products",
    "total_categories",
    "total_users",
    "total_customers",
    "total_orders",
    "total_revenue",
    "pending_payments"
]

assert all(key in statistics for key in required)

print("\nALL DASHBOARD TESTS PASSED.")

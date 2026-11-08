from fastapi.testclient import TestClient
from getpass import getpass
from app.main import app

client = TestClient(app)

print("Testing without login...")
response = client.get("/api/admin/whatsapp-status")
print("Unauthenticated status:", response.status_code)

email = input("Admin email: ")
password = getpass("Admin password: ")

login = client.post(
    "/api/auth/login",
    json={"email": email, "password": password}
)

print("Login status:", login.status_code)

if login.status_code == 200:
    response = client.get("/api/admin/whatsapp-status")
    print("Admin access status:", response.status_code)
    print("WhatsApp status:", response.json())
else:
    print("Login failed. Check your credentials.")

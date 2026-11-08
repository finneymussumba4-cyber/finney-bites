from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import NewsletterSubscriber, ContactMessage

client = TestClient(app)
email = f"test_{uuid4().hex[:10]}@example.com"

try:
    newsletter = client.post(
        "/api/newsletter/subscribe",
        json={"email": email}
    )
    print("NEWSLETTER:", newsletter.status_code, newsletter.json())

    contact = client.post(
        "/api/contact/",
        json={
            "name": "Test Customer",
            "email": email,
            "phone": "0712345678",
            "subject": "Test enquiry",
            "message": "This is a test contact message."
        }
    )
    print("CONTACT:", contact.status_code, contact.json())

    reviews = client.get("/api/reviews/")
    print("REVIEWS:", reviews.status_code, reviews.json())

finally:
    db = SessionLocal()
    try:
        db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.email == email
        ).delete()
        db.query(ContactMessage).filter(
            ContactMessage.email == email
        ).delete()
        db.commit()
        print("TEST DATA CLEANED")
    finally:
        db.close()

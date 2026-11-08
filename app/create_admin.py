from getpass import getpass
from pwdlib import PasswordHash
from app.database import SessionLocal
from app.models import User


def create_admin():
    print("\nFINNEY BITES ADMIN REGISTRATION")

    full_name = input("Administrator full name: ").strip()
    email = input("Administrator email: ").strip().lower()
    phone = input("Administrator phone: ").strip()

    password = getpass("Create password (minimum 12 characters): ")
    confirm_password = getpass("Confirm password: ")

    if not full_name or not email or not phone:
        print("ERROR: All details are required.")
        return

    if len(password) < 12:
        print("ERROR: Password must contain at least 12 characters.")
        return

    if password != confirm_password:
        print("ERROR: Passwords do not match.")
        return

    db = SessionLocal()

    try:
        existing = db.query(User).filter(
            (User.email == email) | (User.phone == phone)
        ).first()

        if existing:
            print("ERROR: This email or phone number is already registered.")
            return

        password_hash = PasswordHash.recommended().hash(password)

        admin = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash=password_hash,
            role="admin",
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print("\nADMIN ACCOUNT CREATED SUCCESSFULLY!")
        print("Name:", admin.full_name)
        print("Email:", admin.email)
        print("Role:", admin.role)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()

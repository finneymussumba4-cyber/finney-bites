from fastapi import APIRouter, Depends, HTTPException, Request
import hashlib, secrets, smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from itsdangerous import URLSafeTimedSerializer

from app.database import get_db
from app.models import User, PasswordResetToken
from app.security import verify_supabase_access_token
from app.config import SECRET_KEY, SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL, SMTP_ENABLED, FRONTEND_URL
from app.schemas.auth import LoginRequest, RegisterRequest, ForgotPasswordRequest, ResetPasswordRequest

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

password_hasher = PasswordHash.recommended()
serializer = URLSafeTimedSerializer(SECRET_KEY)


def normalize_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())

    if digits.startswith("0"):
        return "254" + digits[1:]

    if digits.startswith("254"):
        return digits

    return digits


def create_session_response(user: User, message: str):
    result = JSONResponse(content={
        "message": message,
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role
        }
    })

    result.set_cookie(
        key="finney_session",
        value=serializer.dumps({"user_id": user.id}),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=3600
    )

    return result


@router.post("/register", status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    raise HTTPException(status_code=403, detail="Customer registration must use the secure registration page.")
    email = str(data.email).lower()
    phone = normalize_phone(data.phone)

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    for existing_user in db.query(User).all():
        if normalize_phone(existing_user.phone) == phone:
            raise HTTPException(status_code=409, detail="Phone number already registered")

    user = User(
        full_name=data.full_name.strip(),
        email=email,
        phone=phone,
        password_hash=password_hasher.hash(data.password),
        role="customer",
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return create_session_response(user, "Account created successfully")


@router.post("/login")
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = None

    if data.email:
        user = db.query(User).filter(
            User.email == str(data.email).lower()
        ).first()

    elif data.phone:
        phone = normalize_phone(data.phone)

        for existing_user in db.query(User).all():
            if normalize_phone(existing_user.phone) == phone:
                user = existing_user
                break

    if user and user.role != "admin":
        raise HTTPException(status_code=403, detail="Customer accounts must sign in using Supabase.")

    if not user or not password_hasher.verify(
        data.password, user.password_hash
    ):
        raise HTTPException(status_code=401, detail="Invalid login details")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    return create_session_response(user, "Login successful")


@router.post("/logout")
def logout():
    result = JSONResponse(
        content={"message": "Logged out successfully"}
    )
    result.delete_cookie("finney_session")
    return result


def send_password_reset_email(email: str, reset_link: str):
    message = EmailMessage()
    message["Subject"] = "FINNEY BITES - Password Reset"
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = email

    message.set_content(
        f"""Hello,

We received a request to reset your FINNEY BITES account password.

Use this link to reset your password:
{reset_link}

This link expires in 30 minutes and can only be used once.

If you did not request this, you can ignore this email.

FINNEY BITES
Fresh Food, Fast Delivery!
"""
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()



@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    generic_message = (
        "If an account exists with that email, password reset instructions will be sent."
    )

    if not SMTP_ENABLED:
        return {"message": generic_message}

    email = str(data.email).lower()
    user = db.query(User).filter(User.email == email).first()

    if not user or not user.is_active:
        return {"message": generic_message}

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None)
    ).update({"used_at": now})

    raw_token = secrets.token_urlsafe(32)

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_reset_token(raw_token),
        expires_at=now + timedelta(minutes=30)
    )

    db.add(reset_record)
    db.commit()

    try:
        reset_link = (
            f"{FRONTEND_URL.rstrip('/')}/reset-password.html?token={raw_token}"
        )
        send_password_reset_email(user.email, reset_link)
    except Exception:
        db.delete(reset_record)
        db.commit()

    return {"message": generic_message}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_hash = hash_reset_token(data.token)

    reset_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash
    ).first()

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if (
        not reset_record
        or reset_record.used_at is not None
        or reset_record.expires_at <= now
    ):
        raise HTTPException(
            status_code=400,
            detail="This password reset link is invalid or has expired."
        )

    user = db.query(User).filter(
        User.id == reset_record.user_id,
        User.is_active.is_(True)
    ).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="This password reset link is invalid or has expired."
        )

    user.password_hash = password_hasher.hash(data.new_password)
    reset_record.used_at = now

    # Invalidate any other outstanding reset links for this account.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.id != reset_record.id,
        PasswordResetToken.used_at.is_(None)
    ).update({"used_at": now})

    db.commit()

    return {"message": "Password reset successful. Please sign in again."}




@router.post("/supabase-session")
def create_supabase_customer_session(
    request: Request,
    db: Session = Depends(get_db)
):
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please sign in.")

    auth_user = verify_supabase_access_token(authorization[7:].strip())

    supabase_id = auth_user.get("id")
    email = (auth_user.get("email") or "").strip().lower()
    metadata = auth_user.get("user_metadata") or {}

    if not supabase_id or not email:
        raise HTTPException(status_code=401, detail="Invalid account details.")

    user = db.query(User).filter(User.email.ilike(email)).first()

    if user:
        if user.role != "customer":
            raise HTTPException(status_code=403, detail="Administrator accounts cannot use customer access.")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Customer account unavailable.")
        if user.supabase_user_id and user.supabase_user_id != supabase_id:
            raise HTTPException(status_code=403, detail="This account is already linked to another login.")
        user.supabase_user_id = supabase_id
    else:
        full_name = (metadata.get("full_name") or "").strip()
        phone = normalize_phone(metadata.get("phone") or "")

        if len(full_name) < 2 or not phone:
            raise HTTPException(status_code=400, detail="Your name and phone number are required. Please register again.")

        phone_owner = db.query(User).filter(User.phone == phone).first()
        if phone_owner:
            raise HTTPException(status_code=409, detail="This phone number is already registered. Please contact support.")

        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash=password_hasher.hash(secrets.token_urlsafe(32)),
            role="customer",
            is_active=True,
            supabase_user_id=supabase_id
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    return {
        "message": "Customer account verified successfully.",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role
        }
    }

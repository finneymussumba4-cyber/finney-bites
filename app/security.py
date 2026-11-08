from fastapi import Depends, HTTPException, Request
import httpx
from sqlalchemy.orm import Session
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.config import SECRET_KEY, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY
from app.database import get_db
from app.models import User

serializer = URLSafeTimedSerializer(SECRET_KEY)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("finney_session")

    if not token:
        raise HTTPException(status_code=401, detail="Please log in")

    try:
        data = serializer.loads(token, max_age=3600)
        user_id = data.get("user_id")

    except (BadSignature, SignatureExpired):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    if not isinstance(user_id, int):
        raise HTTPException(status_code=401, detail="Invalid session")

    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Account unavailable")

    return user


def get_current_admin(
    user: User = Depends(get_current_user)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    return user

def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("finney_session")

    if not token:
        return None

    try:
        data = serializer.loads(token, max_age=3600)
        user_id = data.get("user_id")
    except (BadSignature, SignatureExpired):
        return None

    if not isinstance(user_id, int):
        return None

    user = db.query(User).filter(
        User.id == user_id,
        User.is_active == True
    ).first()

    return user


def verify_supabase_access_token(access_token: str) -> dict:
    if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
        raise HTTPException(
            status_code=503,
            detail="Authentication service is not configured"
        )

    try:
        response = httpx.get(
            f"{SUPABASE_URL.rstrip('/')}/auth/v1/user",
            headers={
                "apikey": SUPABASE_PUBLISHABLE_KEY,
                "Authorization": f"Bearer {access_token}"
            },
            timeout=10
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Authentication service is temporarily unavailable"
        )

    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired login session"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=503,
            detail="Could not verify login session"
        )

    auth_user = response.json()

    if not auth_user.get("email_confirmed_at") and not auth_user.get("confirmed_at"):
        raise HTTPException(
            status_code=403,
            detail="Please confirm your email address before signing in"
        )

    return auth_user


def get_current_customer(
    request: Request,
    db: Session = Depends(get_db)
):
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please sign in")

    access_token = authorization[7:].strip()
    if not access_token:
        raise HTTPException(status_code=401, detail="Please sign in")

    auth_user = verify_supabase_access_token(access_token)
    supabase_id = auth_user.get("id")
    email = (auth_user.get("email") or "").strip().lower()

    if not supabase_id or not email:
        raise HTTPException(status_code=401, detail="Invalid account details")

    user = db.query(User).filter(
        User.supabase_user_id == supabase_id
    ).first()

    if not user:
        user = db.query(User).filter(
            User.email == email
        ).first()

        if not user:
            raise HTTPException(
                status_code=403,
                detail="Please complete your FINNEY BITES account registration"
            )

        if user.role != "customer":
            raise HTTPException(
                status_code=403,
                detail="Administrator accounts cannot use customer access"
            )

        if user.supabase_user_id:
            raise HTTPException(
                status_code=403,
                detail="This account is already linked to another login"
            )

        user.supabase_user_id = supabase_id
        db.commit()
        db.refresh(user)

    if user.role != "customer" or not user.is_active:
        raise HTTPException(status_code=403, detail="Customer account unavailable")

    return user

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Order, CustomerPreference, CustomerAddress, CustomerNotification
from app.security import get_current_customer

router = APIRouter(prefix="/api/customer", tags=["Customer Account"])


@router.get("/profile")
def customer_profile(
    user: User = Depends(get_current_customer)
):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "created_at": user.created_at
    }


@router.get("/orders")
def customer_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_customer)
):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return [
        {
            "order_number": order.order_number,
            "order_type": order.order_type,
            "delivery_zone_id": order.delivery_zone_id,
            "delivery_address": order.delivery_address,
            "mpesa_reference": order.mpesa_reference,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "status": order.status,
            "payment_status": order.payment_status,
            "subtotal": order.subtotal,
            "discount_amount": order.discount_amount,
            "delivery_fee": order.delivery_fee,
            "total_amount": order.total_amount,
            "created_at": order.created_at,
            "items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "line_total": item.line_total
                }
                for item in order.items
            ]
        }
        for order in orders
    ]

from app.models import CustomerLoyalty


@router.get("/loyalty")
def customer_loyalty(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_customer)
):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    loyalty = db.query(CustomerLoyalty).filter(
        CustomerLoyalty.user_id == user.id
    ).first()

    if not loyalty:
        return {
            "completed_orders": 0,
            "points_balance": 0,
            "lifetime_points": 0,
            "orders_until_reward": 6
        }

    return {
        "completed_orders": loyalty.completed_orders,
        "points_balance": loyalty.points_balance,
        "lifetime_points": loyalty.lifetime_points,
        "orders_until_reward": 6 - (loyalty.completed_orders % 6)
    }

from app.models import CustomerFavorite, Product


@router.post("/favorites/{product_id}")
def add_favorite(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_customer)
):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Meal not found")

    existing = db.query(CustomerFavorite).filter(
        CustomerFavorite.user_id == user.id,
        CustomerFavorite.product_id == product_id
    ).first()

    if existing:
        return {"message": "Meal is already in your favourites"}

    favorite = CustomerFavorite(
        user_id=user.id,
        product_id=product_id
    )

    db.add(favorite)
    db.commit()

    return {
        "message": "Meal added to favourites",
        "product_id": product_id,
        "product_name": product.name
    }


@router.get("/favorites")
def get_favorites(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_customer)
):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    favorites = (
        db.query(CustomerFavorite, Product)
        .join(Product, CustomerFavorite.product_id == Product.id)
        .filter(CustomerFavorite.user_id == user.id)
        .order_by(CustomerFavorite.created_at.desc())
        .all()
    )

    return [
        {
            "product_id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "image": product.image,
            "is_available": product.is_available
        }
        for favorite, product in favorites
    ]


@router.delete("/favorites/{product_id}")
def remove_favorite(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_customer)
):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    favorite = db.query(CustomerFavorite).filter(
        CustomerFavorite.user_id == user.id,
        CustomerFavorite.product_id == product_id
    ).first()

    if not favorite:
        raise HTTPException(status_code=404, detail="Favourite not found")

    db.delete(favorite)
    db.commit()

    return {"message": "Meal removed from favourites"}


@router.get("/preferences")
def get_customer_preferences(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_customer)
):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    preferences = db.query(CustomerPreference).filter(
        CustomerPreference.user_id == user.id
    ).first()

    if not preferences:
        return {
            "preferred_delivery_location": None,
            "favorite_categories": [],
            "recently_viewed": [],
            "display_preferences": {}
        }

    return {
        "preferred_delivery_location": preferences.preferred_delivery_location,
        "favorite_categories": preferences.favorite_categories,
        "recently_viewed": preferences.recently_viewed,
        "display_preferences": preferences.display_preferences
    }


@router.put("/preferences")
def update_customer_preferences(
    data: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_customer)
):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    allowed_fields = {
        "preferred_delivery_location",
        "favorite_categories",
        "recently_viewed",
        "display_preferences"
    }

    if not data or not set(data).issubset(allowed_fields):
        raise HTTPException(status_code=400, detail="Invalid preference fields")

    if "favorite_categories" in data:
        if not isinstance(data["favorite_categories"], list):
            raise HTTPException(status_code=400, detail="Categories must be a list")
        if len(data["favorite_categories"]) > 20:
            raise HTTPException(status_code=400, detail="Too many categories")

    if "recently_viewed" in data:
        if not isinstance(data["recently_viewed"], list):
            raise HTTPException(status_code=400, detail="Recently viewed must be a list")
        if len(data["recently_viewed"]) > 30:
            raise HTTPException(status_code=400, detail="Too many recently viewed meals")

    if "display_preferences" in data:
        if not isinstance(data["display_preferences"], dict):
            raise HTTPException(status_code=400, detail="Display preferences must be an object")

    if "preferred_delivery_location" in data:
        location = data["preferred_delivery_location"]
        if location is not None and (
            not isinstance(location, str) or len(location) > 100
        ):
            raise HTTPException(status_code=400, detail="Invalid delivery location")

    preferences = db.query(CustomerPreference).filter(
        CustomerPreference.user_id == user.id
    ).first()

    if not preferences:
        preferences = CustomerPreference(user_id=user.id)
        db.add(preferences)

    for field, value in data.items():
        setattr(preferences, field, value)

    db.commit()

    return {"message": "Customer preferences saved successfully"}


from pwdlib import PasswordHash

customer_password_hasher = PasswordHash.recommended()


@router.get("/addresses")
def get_addresses(db: Session = Depends(get_db), user: User = Depends(get_current_customer)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")
    return db.query(CustomerAddress).filter(
        CustomerAddress.user_id == user.id
    ).order_by(CustomerAddress.is_default.desc()).all()


@router.post("/addresses")
def add_address(data: dict, db: Session = Depends(get_db), user: User = Depends(get_current_customer)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    required = ["recipient_name", "phone", "county", "town", "estate"]
    if any(not str(data.get(field, "")).strip() for field in required):
        raise HTTPException(status_code=400, detail="Complete all required address fields")

    if data.get("is_default"):
        db.query(CustomerAddress).filter(
            CustomerAddress.user_id == user.id
        ).update({"is_default": False})

    address = CustomerAddress(
        user_id=user.id,
        label=data.get("label", "Home"),
        recipient_name=data["recipient_name"].strip(),
        phone=data["phone"].strip(),
        county=data["county"].strip(),
        town=data["town"].strip(),
        estate=data["estate"].strip(),
        building=data.get("building"),
        house_number=data.get("house_number"),
        instructions=data.get("instructions"),
        is_default=data.get("is_default", False)
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return {"message": "Address saved", "id": address.id}


@router.put("/addresses/{address_id}")
def update_address(address_id: int, data: dict, db: Session = Depends(get_db), user: User = Depends(get_current_customer)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    address = db.query(CustomerAddress).filter(
        CustomerAddress.id == address_id,
        CustomerAddress.user_id == user.id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    allowed = ["label", "recipient_name", "phone", "county", "town", "estate",
               "building", "house_number", "instructions"]

    for field in allowed:
        if field in data:
            setattr(address, field, data[field])

    if data.get("is_default"):
        db.query(CustomerAddress).filter(
            CustomerAddress.user_id == user.id
        ).update({"is_default": False})
        address.is_default = True

    db.commit()
    return {"message": "Address updated"}


@router.delete("/addresses/{address_id}")
def delete_address(address_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_customer)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    address = db.query(CustomerAddress).filter(
        CustomerAddress.id == address_id,
        CustomerAddress.user_id == user.id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    db.delete(address)
    db.commit()
    return {"message": "Address deleted"}


@router.post("/addresses/{address_id}/default")
def set_default_address(address_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_customer)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    address = db.query(CustomerAddress).filter(
        CustomerAddress.id == address_id,
        CustomerAddress.user_id == user.id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    db.query(CustomerAddress).filter(
        CustomerAddress.user_id == user.id
    ).update({"is_default": False})

    address.is_default = True
    db.commit()
    return {"message": "Default address updated"}


@router.get("/payments")
def customer_payment_history(db: Session = Depends(get_db), user: User = Depends(get_current_customer)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    orders = db.query(Order).filter(
        Order.user_id == user.id
    ).order_by(Order.created_at.desc()).all()

    return [{
        "order_number": order.order_number,
            "order_type": order.order_type,
            "delivery_zone_id": order.delivery_zone_id,
            "delivery_address": order.delivery_address,
            "mpesa_reference": order.mpesa_reference,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
        "date": order.created_at,
        "amount": order.total_amount,
        "payment_status": order.payment_status,
        "mpesa_reference": order.mpesa_reference,
        "order_status": order.status
    } for order in orders]


@router.get("/notifications")
def customer_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_customer)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    notifications = db.query(CustomerNotification).filter(
        CustomerNotification.user_id == user.id
    ).order_by(CustomerNotification.created_at.desc()).all()

    return {
        "unread_count": sum(notice.is_read is False for notice in notifications),
        "notifications": notifications
    }


@router.put("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_customer)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    notice = db.query(CustomerNotification).filter(
        CustomerNotification.id == notification_id,
        CustomerNotification.user_id == user.id
    ).first()

    if not notice:
        raise HTTPException(status_code=404, detail="Notification not found")

    notice.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}


@router.post("/notifications/read-all")
def mark_all_notifications_read(db: Session = Depends(get_db), user: User = Depends(get_current_customer)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    db.query(CustomerNotification).filter(
        CustomerNotification.user_id == user.id
    ).update({"is_read": True})

    db.commit()
    return {"message": "All notifications marked as read"}


@router.put("/profile")
def update_customer_profile(data: dict, db: Session = Depends(get_db), user: User = Depends(get_current_customer)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    if "full_name" in data:
        if not str(data["full_name"]).strip():
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        user.full_name = data["full_name"].strip()

    if "email" in data:
        email = data["email"].strip().lower()
        existing = db.query(User).filter(
            User.email == email, User.id != user.id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        user.email = email

    if "phone" in data:
        user.phone = data["phone"].strip()

    db.commit()
    return {"message": "Profile updated"}


@router.put("/password")
def change_customer_password(data: dict, db: Session = Depends(get_db), user: User = Depends(get_current_customer)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")

    current = data.get("current_password", "")
    new = data.get("new_password", "")

    if not current or not new:
        raise HTTPException(status_code=400, detail="Both passwords are required")

    if not customer_password_hasher.verify(current, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if len(new) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    user.password_hash = customer_password_hasher.hash(new)
    db.commit()
    return {"message": "Password updated successfully"}



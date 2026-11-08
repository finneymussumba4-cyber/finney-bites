from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, CustomerPreference, User
from app.schemas.product import ProductResponse
from app.security import get_optional_current_user

router = APIRouter(
    prefix="/api/products",
    tags=["Products"]
)


@router.get("/", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return (
        db.query(Product)
        .filter(Product.is_available == True)
        .order_by(Product.name)
        .all()
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user)
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_available == True
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Meal not found")

    if user and user.role == "customer":
        preferences = db.query(CustomerPreference).filter(
            CustomerPreference.user_id == user.id
        ).first()

        if not preferences:
            preferences = CustomerPreference(
                user_id=user.id,
                recently_viewed=[]
            )
            db.add(preferences)
            db.flush()

        viewed = preferences.recently_viewed or []
        viewed = [item for item in viewed if item != product_id]
        viewed.insert(0, product_id)

        preferences.recently_viewed = viewed[:30]
        db.commit()

    return product

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category
from app.schemas.category import CategoryResponse

router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"]
)


@router.get("/", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return (
        db.query(Category)
        .filter(Category.is_active == True)
        .order_by(Category.name)
        .all()
    )
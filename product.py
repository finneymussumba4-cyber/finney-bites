from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional


class ProductResponse(BaseModel):
    id: int
    category_id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    image: Optional[str] = None
    stock_quantity: int
    is_available: bool
    is_featured: bool

    model_config = ConfigDict(from_attributes=True)
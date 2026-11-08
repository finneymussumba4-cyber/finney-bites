from pydantic import BaseModel, ConfigDict, Field
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


class ProductCreate(BaseModel):
    category_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, max_length=1000)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    image: Optional[str] = None
    stock_quantity: int = Field(default=0, ge=0)
    is_available: bool = True
    is_featured: bool = False


class ProductUpdate(BaseModel):
    category_id: Optional[int] = Field(default=None, gt=0)
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, max_length=1000)
    price: Optional[Decimal] = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    image: Optional[str] = None
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    is_available: Optional[bool] = None
    is_featured: Optional[bool] = None

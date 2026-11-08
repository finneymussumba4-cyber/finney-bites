from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=50)


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=150)
    customer_phone: str = Field(min_length=9, max_length=20)
    customer_email: Optional[str] = None

    order_type: str = Field(pattern="^(delivery|pickup)$")
    delivery_zone_id: Optional[int] = None
    delivery_address: Optional[str] = None

    notes: Optional[str] = Field(default=None, max_length=500)
    items: list[OrderItemCreate] = Field(min_length=1, max_length=30)


class OrderItemResponse(BaseModel):
    product_name: str
    unit_price: float
    quantity: int
    line_total: float

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    order_number: str
    customer_name: str
    order_type: str
    subtotal: float
    discount_amount: float
    delivery_fee: float
    total_amount: float
    status: str
    payment_status: str
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)

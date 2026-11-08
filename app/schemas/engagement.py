from pydantic import BaseModel, EmailStr, Field


class ReviewCreate(BaseModel):
    customer_phone: str = Field(min_length=9, max_length=20)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=5, max_length=1000)


class NewsletterSubscribe(BaseModel):
    email: EmailStr


class ContactCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    subject: str = Field(min_length=2, max_length=200)
    message: str = Field(min_length=10, max_length=3000)

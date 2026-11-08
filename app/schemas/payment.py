from pydantic import BaseModel, Field

class PaymentReferenceSubmit(BaseModel):
    customer_phone: str = Field(min_length=9, max_length=20)
    mpesa_reference: str = Field(
        min_length=8,
        max_length=20,
        pattern="^[A-Za-z0-9]+$"
    )

class PaymentVerification(BaseModel):
    mpesa_reference: str
    received_amount: float = Field(gt=0)
    confirmed_in_statement: bool

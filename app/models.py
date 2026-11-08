from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String, Integer, Boolean, DateTime, Text, JSON,
    ForeignKey, Numeric, func, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    phone: Mapped[str] = mapped_column(
        String(20), unique=True
    )
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        String(20), default="customer"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    supabase_user_id: Mapped[str | None] = mapped_column(
        String(36), unique=True, nullable=True, index=True
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True
    )
    description: Mapped[str | None] = mapped_column(Text)
    image: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True
    )

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id")
    )
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    image: Mapped[str | None] = mapped_column(String(255))
    stock_quantity: Mapped[int] = mapped_column(
        Integer, default=0
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean, default=True
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    category = relationship("Category", back_populates="products")


class DeliveryZone(Base):
    __tablename__ = "delivery_zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True
    )


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(
        String(100), unique=True
    )
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )


class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id")
    )
    change_quantity: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    customer_name: Mapped[str] = mapped_column(String(150))
    customer_phone: Mapped[str] = mapped_column(String(20))
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    order_type: Mapped[str] = mapped_column(String(20))
    delivery_zone_id: Mapped[int | None] = mapped_column(
        ForeignKey("delivery_zones.id"), nullable=True
    )
    delivery_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    status: Mapped[str] = mapped_column(String(30), default="received")
    payment_status: Mapped[str] = mapped_column(String(30), default="unverified")
    mpesa_reference: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True
    )

    mpesa_checkout_request_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    mpesa_merchant_request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mpesa_receipt_number: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    mpesa_phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mpesa_paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    stock_deducted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))

    product_name: Mapped[str] = mapped_column(String(150))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer)
    line_total: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), unique=True
    )
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    subject: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(30), default="new"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class CustomerLoyalty(Base):
    __tablename__ = "customer_loyalty"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_phone: Mapped[str] = mapped_column(
        String(20), unique=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=True
    )
    completed_orders: Mapped[int] = mapped_column(
        Integer, default=0
    )
    points_balance: Mapped[int] = mapped_column(
        Integer, default=0
    )
    lifetime_points: Mapped[int] = mapped_column(
        Integer, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class CustomerFavorite(Base):
    __tablename__ = "customer_favorites"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "product_id",
            name="uq_customer_favorite_user_product"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

class CustomerPreference(Base):
    __tablename__ = "customer_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, index=True
    )

    preferred_delivery_location: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    favorite_categories: Mapped[list] = mapped_column(
        JSON, default=list
    )

    recently_viewed: Mapped[list] = mapped_column(
        JSON, default=list
    )

    display_preferences: Mapped[dict] = mapped_column(
        JSON, default=dict
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

class CustomerAddress(Base):
    __tablename__ = "customer_addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    label: Mapped[str] = mapped_column(String(50), default="Home")
    recipient_name: Mapped[str] = mapped_column(String(150))
    phone: Mapped[str] = mapped_column(String(20))
    county: Mapped[str] = mapped_column(String(100))
    town: Mapped[str] = mapped_column(String(100))
    estate: Mapped[str] = mapped_column(String(150))
    building: Mapped[str | None] = mapped_column(String(150), nullable=True)
    house_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

class CustomerNotification(Base):
    __tablename__ = "customer_notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(150))
    message: Mapped[str] = mapped_column(Text)
    notification_type: Mapped[str] = mapped_column(
        String(50), default="general"
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
 
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

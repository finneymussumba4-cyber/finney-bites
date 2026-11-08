from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo
import secrets

from sqlalchemy.orm import Session

from app.config import BUSINESS_SETTINGS
from app.models import Product, DeliveryZone, Order, OrderItem


CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value):
    return Decimal(str(value)).quantize(
        CENT, rounding=ROUND_HALF_UP
    )


def create_order(db: Session, data, user_id=None):
    try:
        if data.order_type not in ("delivery", "pickup"):
            raise ValueError("Invalid order type")

        if not data.items:
            raise ValueError("Your order must contain products")

        # Combine repeated product IDs.
        quantities = {}
        for item in data.items:
            if item.quantity <= 0:
                raise ValueError("Invalid product quantity")
            quantities[item.product_id] = (
                quantities.get(item.product_id, 0) + item.quantity
            )

        subtotal = ZERO
        discount = ZERO
        order_items = []

        # Kenya local date determines Friday promotion.
        local_now = datetime.now(
            ZoneInfo(BUSINESS_SETTINGS["timezone"])
        )
        friday_promotion = local_now.month == 11 and local_now.weekday() == 4 and local_now.day >= 25

        for product_id, quantity in quantities.items():
            product = db.query(Product).filter(
                Product.id == product_id
            ).with_for_update().first()

            if not product or not product.is_available:
                raise ValueError(
                    f"Product {product_id} is unavailable"
                )

            if product.stock_quantity < quantity:
                raise ValueError(
                    f"Insufficient stock for {product.name}"
                )

            unit_price = money(product.price)
            line_subtotal = money(unit_price * quantity)

            line_discount = ZERO

            if friday_promotion and unit_price > Decimal("700.00"):
                line_discount = money(
                    line_subtotal * Decimal("0.40")
                )

            subtotal += line_subtotal
            discount += line_discount

            order_items.append({
                "product_id": product.id,
                "product_name": product.name,
                "unit_price": unit_price,
                "quantity": quantity,
                "line_total": money(
                    line_subtotal - line_discount
                )
            })

        subtotal = money(subtotal)
        discount = money(discount)

        delivery_fee = ZERO
        delivery_zone = None

        if data.order_type == "delivery":
            if not data.delivery_zone_id:
                raise ValueError("Select a delivery zone")

            if not data.delivery_address:
                raise ValueError("Enter your delivery address")

            delivery_zone = db.query(DeliveryZone).filter(
                DeliveryZone.id == data.delivery_zone_id,
                DeliveryZone.is_active == True
            ).first()

            if not delivery_zone:
                raise ValueError("Invalid delivery zone")

            free_minimum = Decimal(
                str(BUSINESS_SETTINGS["free_delivery_minimum"])
            )

            if subtotal < free_minimum:
                delivery_fee = money(delivery_zone.delivery_fee)

        elif data.order_type == "pickup":
            if data.delivery_zone_id or data.delivery_address:
                raise ValueError(
                    "Pickup orders cannot have delivery details"
                )

        total = money(subtotal - discount + delivery_fee)

        order_number = (
            "FB-" + local_now.strftime("%Y%m%d") +
            "-" + secrets.token_hex(3).upper()
        )

        order = Order(
            order_number=order_number,
            user_id=user_id,
            customer_name=data.customer_name.strip(),
            customer_phone=data.customer_phone.strip(),
            customer_email=data.customer_email,
            order_type=data.order_type,
            delivery_zone_id=(
                delivery_zone.id if delivery_zone else None
            ),
            delivery_address=data.delivery_address,
            subtotal=subtotal,
            discount_amount=discount,
            delivery_fee=delivery_fee,
            total_amount=total,
            status="received",
            payment_status="unverified",
            stock_deducted=False,
            notes=data.notes
        )

        for item in order_items:
            order.items.append(OrderItem(**item))

        db.add(order)
        db.commit()
        db.refresh(order)

        return order

    except Exception:
        db.rollback()
        raise


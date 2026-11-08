from pathlib import Path
from app.database import SessionLocal
from app.models import Product

IMAGE_MAP = {
    1: "bbq-burger.jpg",
    2: "cheese-burger.jpg",
    3: "chicken-burger.jpg",
    4: "double-burger.jpg",
    5: "bbq-burger.jpg",
    6: "french-fries.jpg",
    7: "french-fries.jpg",
    8: "masala-chips.jpg",
    9: "masala-chips.jpg",
    10: "sweet-potato-fries.jpg",
    11: "fried-chicken.jpg",
    12: "fried-chicken.jpg",
    13: "chicken-wings.jpg",
    14: "chicken-nuggets.jpg",
    15: "chicken-strips.jpg",
    16: "samosa.jpg",
    17: "sausage-roll.jpg",
    18: "sausage-roll.jpg",
    19: "hot-dog.jpg",
    20: "hot-dog.jpg",
    21: "margherita-pizza.jpg",
    22: "chicken-pizza.jpg",
    23: "meat-lovers-pizza.jpg",
    24: "chicken-pizza.jpg",
    25: "supreme-pizza.jpg",
    26: "coca-cola.jpg",
    27: "water.jpg",
    28: "fresh-juice.jpg",
    29: "water.jpg",
    30: "beef-burger-chips.jpg",
    31: "chicken-burger.jpg",
    32: "grilled-chicken.jpg",
    33: "hot-dog.jpg",
    34: "double-burger.jpg",
    35: "cheese-burger.jpg",
    36: "cheese-burger.jpg",
}

image_dir = Path("public/images/products")
db = SessionLocal()

try:
    products = db.query(Product).all()

    if len(products) != 36:
        raise ValueError(f"Expected 36 products, found {len(products)}")

    for product_id, filename in IMAGE_MAP.items():
        if not (image_dir / filename).is_file():
            raise FileNotFoundError(filename)

        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        if not product:
            raise ValueError(f"Product ID {product_id} not found")

        product.image = f"/images/products/{filename}"

    db.commit()
    print("SUCCESS: Images assigned to all 36 products.")

except Exception:
    db.rollback()
    raise

finally:
    db.close()

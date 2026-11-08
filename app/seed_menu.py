from decimal import Decimal

from app.database import SessionLocal
from app.models import Category, Product

MENU = {
    "Burgers": [
        ("Classic Beef Burger", 500),
        ("Cheese Beef Burger", 600),
        ("Chicken Burger", 550),
        ("Double Beef Burger", 750),
        ("Special Finney Burger", 850),
    ],
    "Fries": [
        ("Plain Chips", 200),
        ("Large Chips", 300),
        ("Masala Chips", 250),
        ("Large Masala Chips", 350),
        ("Potato Wedges", 250),
    ],
    "Chicken": [
        ("Fried Chicken - 1 Piece", 350),
        ("Fried Chicken - 2 Pieces", 650),
        ("Chicken Wings - 6 Pieces", 500),
        ("Chicken Nuggets - 6 Pieces", 450),
        ("Chicken Strips", 500),
    ],
    "Snacks": [
        ("Beef Samosas - 2 Pieces", 150),
        ("Sausages - 2 Pieces", 180),
        ("Beef Sausage", 100),
        ("Classic Hot Dog", 300),
        ("Loaded Hot Dog", 450),
    ],
    "Pizza": [
        ("Margherita Pizza", 650),
        ("Chicken Pizza", 850),
        ("Beef Pizza", 850),
        ("Chicken Tikka Pizza", 950),
        ("Special Finney Pizza", 1100),
    ],
    "Drinks": [
        ("Soda", 100),
        ("Bottled Water", 100),
        ("Fresh Juice", 200),
        ("Mineral Water - Large", 150),
    ],
    "Combos": [
        ("Beef Burger + Chips", 650),
        ("Chicken Burger + Chips", 700),
        ("Chicken + Chips", 600),
        ("Hot Dog + Chips", 500),
        ("Double Burger Combo", 950),
    ],
}


def seed_menu():
    db = SessionLocal()

    try:
        added_categories = 0
        added_products = 0
        updated_products = 0

        for category_name, products in MENU.items():
            category = db.query(Category).filter(
                Category.name == category_name
            ).first()

            if not category:
                category = Category(
                    name=category_name,
                    description=f"{category_name} at FINNEY BITES",
                    is_active=True,
                )
                db.add(category)
                db.flush()
                added_categories += 1

            for product_name, price in products:
                product = db.query(Product).filter(
                    Product.category_id == category.id,
                    Product.name == product_name,
                ).first()

                if product:
                    product.price = Decimal(str(price))
                    updated_products += 1
                else:
                    product = Product(
                        category_id=category.id,
                        name=product_name,
                        description=f"Freshly prepared {product_name} from FINNEY BITES.",
                        price=Decimal(str(price)),
                        stock_quantity=10,
                        is_available=True,
                        is_featured=False,
                    )
                    db.add(product)
                    added_products += 1

        db.commit()

        print("FINNEY BITES MENU SEEDING SUCCESSFUL")
        print(f"Categories added: {added_categories}")
        print(f"Products added: {added_products}")
        print(f"Existing products updated: {updated_products}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_menu()

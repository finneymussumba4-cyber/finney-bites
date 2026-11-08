from decimal import Decimal
from app.database import SessionLocal
from app.models import DeliveryZone

ZONES = {
    "Ruiru Town": 100,
    "Kimbo": 150,
    "Membley": 150,
    "Kahawa Sukari": 200,
    "Juja": 250,
}

db = SessionLocal()

try:
    added = 0

    for name, fee in ZONES.items():
        zone = db.query(DeliveryZone).filter(
            DeliveryZone.name == name
        ).first()

        if not zone:
            db.add(
                DeliveryZone(
                    name=name,
                    delivery_fee=Decimal(str(fee)),
                    is_active=True
                )
            )
            added += 1

    db.commit()
    print("DELIVERY ZONES SETUP SUCCESSFUL")
    print(f"New zones added: {added}")

except Exception:
    db.rollback()
    raise

finally:
    db.close()

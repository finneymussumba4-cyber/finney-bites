"""Add M-Pesa payment tracking."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "d88205d33a71"
down_revision: Union[str, Sequence[str], None] = "04cca85be3a8"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("orders", sa.Column("mpesa_checkout_request_id", sa.String(100), nullable=True))
    op.add_column("orders", sa.Column("mpesa_merchant_request_id", sa.String(100), nullable=True))
    op.add_column("orders", sa.Column("mpesa_receipt_number", sa.String(50), nullable=True))
    op.add_column("orders", sa.Column("mpesa_phone_number", sa.String(20), nullable=True))
    op.add_column("orders", sa.Column("mpesa_paid_at", sa.DateTime(), nullable=True))
    op.create_index("ix_orders_mpesa_checkout_request_id", "orders", ["mpesa_checkout_request_id"], unique=True)
    op.create_index("ix_orders_mpesa_receipt_number", "orders", ["mpesa_receipt_number"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_orders_mpesa_receipt_number", table_name="orders")
    op.drop_index("ix_orders_mpesa_checkout_request_id", table_name="orders")
    op.drop_column("orders", "mpesa_paid_at")
    op.drop_column("orders", "mpesa_phone_number")
    op.drop_column("orders", "mpesa_receipt_number")
    op.drop_column("orders", "mpesa_merchant_request_id")
    op.drop_column("orders", "mpesa_checkout_request_id")

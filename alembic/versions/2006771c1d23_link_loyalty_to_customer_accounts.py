"""link loyalty to customer accounts

Revision ID: 2006771c1d23
Revises: a469cb125a21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '2006771c1d23'
down_revision: Union[str, Sequence[str], None] = 'a469cb125a21'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table(
        "customer_loyalty",
        recreate="always"
    ) as batch_op:
        batch_op.add_column(
            sa.Column("user_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_customer_loyalty_user_id_users",
            "users",
            ["user_id"],
            ["id"]
        )
        batch_op.create_unique_constraint(
            "uq_customer_loyalty_user_id",
            ["user_id"]
        )


def downgrade() -> None:
    with op.batch_alter_table(
        "customer_loyalty",
        recreate="always"
    ) as batch_op:
        batch_op.drop_constraint(
            "uq_customer_loyalty_user_id",
            type_="unique"
        )
        batch_op.drop_constraint(
            "fk_customer_loyalty_user_id_users",
            type_="foreignkey"
        )
        batch_op.drop_column("user_id")

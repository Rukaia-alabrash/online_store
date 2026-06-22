"""fix receiptstatus enum values

Revision ID: b84f741a2a91
Revises: a14f75fa87bc
Create Date: 2026-06-22 08:10:37.744011

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b84f741a2a91'
down_revision: Union[str, Sequence[str], None] = 'a14f75fa87bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE receiptstatus RENAME TO receiptstatus_old")
    op.execute("""
        CREATE TYPE receiptstatus AS ENUM (
            'pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'
        )
    """)
    op.execute("""
        ALTER TABLE receipts 
        ALTER COLUMN status TYPE receiptstatus 
        USING (
            CASE status::text
                WHEN 'PENDING' THEN 'pending'
                WHEN 'CONFIRMED' THEN 'confirmed'
                WHEN 'PREPARING' THEN 'processing'
                WHEN 'SHIPPED' THEN 'shipped'
                WHEN 'DELIVERED' THEN 'delivered'
                WHEN 'CANCELLED' THEN 'cancelled'
            END
        )::receiptstatus
    """)
    op.execute("DROP TYPE receiptstatus_old")


def downgrade() -> None:
    """Downgrade schema."""
    pass
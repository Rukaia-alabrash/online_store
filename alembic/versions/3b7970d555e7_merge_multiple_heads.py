"""merge multiple heads

Revision ID: 3b7970d555e7
Revises: 235d3e9b9fc2, b84f741a2a91
Create Date: 2026-06-25 21:06:31.644551

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b7970d555e7'
down_revision: Union[str, Sequence[str], None] = ('235d3e9b9fc2', 'b84f741a2a91')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

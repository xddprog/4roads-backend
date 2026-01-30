"""drop order address

Revision ID: 7a2b9d1c3f4e
Revises: 5f3a2e9f1a2b
Create Date: 2026-01-30 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a2b9d1c3f4e'
down_revision: Union[str, Sequence[str], None] = '5f3a2e9f1a2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('orders', 'address')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('orders', sa.Column('address', sa.String(), nullable=True))

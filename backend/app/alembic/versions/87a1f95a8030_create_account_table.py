"""create account table

Revision ID: 87a1f95a8030
Revises: c318481ea46b
Create Date: 2025-12-30 03:37:10.350346

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87a1f95a8030'
down_revision: Union[str, Sequence[str], None] = 'c318481ea46b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

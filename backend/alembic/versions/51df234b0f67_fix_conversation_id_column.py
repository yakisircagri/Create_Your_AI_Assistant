"""fix conversation id column

Revision ID: 51df234b0f67
Revises: cb191c75c912
Create Date: 2026-08-14 15:31:09.450939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51df234b0f67'
down_revision: Union[str, Sequence[str], None] = 'cb191c75c912'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

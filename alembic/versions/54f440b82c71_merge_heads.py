"""merge heads

Revision ID: 54f440b82c71
Revises: cc70047ba97e, a1b2c3d4e5f6
Create Date: 2025-12-13 17:39:42.552161

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54f440b82c71'
down_revision: Union[str, Sequence[str], None] = ('cc70047ba97e', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

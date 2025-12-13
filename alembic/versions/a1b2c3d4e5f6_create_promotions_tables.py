"""create_promotions_tables

Revision ID: a1b2c3d4e5f6
Revises: 27505a70ce3b
Create Date: 2025-12-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '27505a70ce3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Создание таблицы promotions
    op.create_table(
        'promotions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('discount_percent', sa.Float(), nullable=False, comment='Процент скидки (0-100)'),
        sa.Column('starts_at', sa.DateTime(), nullable=False),
        sa.Column('ends_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Создание таблицы promotion_products (связь многие-ко-многим)
    op.create_table(
        'promotion_products',
        sa.Column('promotion_id', sa.UUID(), nullable=False),
        sa.Column('product_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['promotion_id'], ['promotions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('promotion_id', 'product_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('promotion_products')
    op.drop_table('promotions')

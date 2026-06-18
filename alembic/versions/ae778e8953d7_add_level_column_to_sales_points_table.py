"""add_level_column_to_sales_points_table

Revision ID: ae778e8953d7
Revises: 87d74ad32170
Create Date: 2026-06-18 01:18:28.248299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae778e8953d7'
down_revision: Union[str, Sequence[str], None] = '87d74ad32170'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adiciona a coluna level como Integer, permitindo NULL inicialmente
    op.add_column('sales_points', sa.Column('level', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove a coluna level caso seja necessário reverter a migração
    op.drop_column('sales_points', 'level')
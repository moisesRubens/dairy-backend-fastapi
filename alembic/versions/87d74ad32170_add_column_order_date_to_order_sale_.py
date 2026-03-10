"""add_column_order_date_to_order_sale_point_table

Revision ID: 87d74ad32170
Revises: 8845f91abf7b
Create Date: 2026-03-10 01:15:00.636631

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87d74ad32170'
down_revision: Union[str, Sequence[str], None] = '8845f91abf7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('order_sale_point', sa.Column('order_date', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('order_sale_point', 'order_date')

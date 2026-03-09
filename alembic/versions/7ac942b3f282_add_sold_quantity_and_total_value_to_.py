"""add_sold_quantity_and_total_value_to_retiradas_produto_table

Revision ID: 7ac942b3f282
Revises: c93f11f67c09
Create Date: 2026-03-09 14:24:40.751538

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ac942b3f282'
down_revision: Union[str, Sequence[str], None] = 'c93f11f67c09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('retiradas_produto', sa.Column('sold_quantity', sa.Float, nullable=False, server_default='0'))
    op.add_column('retiradas_produto', sa.Column('total_value', sa.Float, nullable=False, server_default='0'))
    op.alter_column('retiradas_produto', 'quantidade', new_column_name='taken_quantity')


def downgrade() -> None:
    op.drop_column('retiradas_produto', 'sold_quantity')
    op.drop_column('retiradas', 'total_value')
    op.alter_column('retiradas_produto', 'taken_quantity', new_column_name='quantidade')

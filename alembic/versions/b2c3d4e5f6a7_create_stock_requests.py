"""create_stock_requests

Tabela das solicitações de reposição de estoque (fluxo de aprovação
vendedor -> admin). Estados: PENDING, APPROVED, REJECTED, CANCELLED.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'stock_requests',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('requested_by_id', sa.Integer(), sa.ForeignKey('sales_points.id', ondelete='SET NULL'), nullable=True),
        sa.Column('target_point_id', sa.Integer(), sa.ForeignKey('sales_points.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unidade', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_by_id', sa.Integer(), sa.ForeignKey('sales_points.id', ondelete='SET NULL'), nullable=True),
        sa.Column('applied_outbound_id', sa.Integer(), sa.ForeignKey('retiradas_produto.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index('ix_stock_requests_status', 'stock_requests', ['status'])
    op.create_index('ix_stock_requests_target_point_id', 'stock_requests', ['target_point_id'])


def downgrade() -> None:
    op.drop_index('ix_stock_requests_target_point_id', table_name='stock_requests')
    op.drop_index('ix_stock_requests_status', table_name='stock_requests')
    op.drop_table('stock_requests')

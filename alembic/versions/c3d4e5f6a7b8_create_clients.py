"""create_clients

Cria a tabela de clientes (CRM) e adiciona orders.client_id para vincular
uma venda a um cliente.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'clients',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('sale_point_id', sa.Integer(),
                  sa.ForeignKey('sales_points.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_clients_sale_point_id', 'clients', ['sale_point_id'])
    # Coluna inteira simples (a FK fica declarada no model para o ORM; o SQLite
    # não impõe FK por padrão e ALTER ADD COLUMN com FK não é suportado).
    op.add_column('orders', sa.Column('client_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('orders') as batch_op:
        batch_op.drop_column('client_id')
    op.drop_index('ix_clients_sale_point_id', table_name='clients')
    op.drop_table('clients')

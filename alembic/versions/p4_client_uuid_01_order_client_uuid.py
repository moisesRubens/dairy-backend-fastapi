"""order client_uuid (idempotência da venda offline)

Revision ID: a1b2c3d4e5f6
Revises: d48269ffbd12
Create Date: 2026-06-17

Aditiva: só adiciona a coluna nullable `client_uuid` em `orders`.
"""
from alembic import op
import sqlalchemy as sa

revision = 'p4_client_uuid_01'
down_revision = 'd48269ffbd12'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('client_uuid', sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'client_uuid')

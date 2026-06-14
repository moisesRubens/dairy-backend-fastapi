"""add_role_to_sales_points

Adiciona a coluna de papel (role) à tabela sales_points para suportar
o controle de acesso ADMIN x VENDEDOR. Contas existentes recebem
"vendedor" por padrão (server_default), preservando o comportamento atual.

Revision ID: a1b2c3d4e5f6
Revises: 87d74ad32170
Create Date: 2026-06-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '87d74ad32170'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'sales_points',
        sa.Column('role', sa.String(20), nullable=False, server_default=sa.text("'vendedor'")),
    )


def downgrade() -> None:
    # SQLite não suporta DROP COLUMN direto: usa modo batch (rebuild da tabela).
    with op.batch_alter_table('sales_points') as batch_op:
        batch_op.drop_column('role')

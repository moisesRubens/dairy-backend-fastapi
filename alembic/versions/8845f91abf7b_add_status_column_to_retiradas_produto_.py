"""add_status_column_to_retiradas_produto_table

Revision ID: 8845f91abf7b
Revises: 7ac942b3f282
Create Date: 2026-03-09 17:20:28.362259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8845f91abf7b'
down_revision: Union[str, Sequence[str], None] = '7ac942b3f282'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('retiradas_produto', sa.Column('status', sa.Boolean, nullable=True, server_default=sa.text('(FALSE)')))


def downgrade() -> None:
    """Downgrade schema."""
    pass

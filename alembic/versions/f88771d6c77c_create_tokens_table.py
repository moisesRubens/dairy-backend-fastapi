"""create tokens table

Revision ID: f88771d6c77c
Revises: 36197da49466
Create Date: 2026-02-12 20:40:42.072338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f88771d6c77c'
down_revision: Union[str, Sequence[str], None] = '36197da49466'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tokens',
        sa.Column("id", sa.String(), primary_key=True))


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""product image_url

Revision ID: d48269ffbd12
Revises: d4e5f6a7b8c9
Create Date: 2026-06-17 12:52:34.702318

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd48269ffbd12'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Migração estritamente aditiva: adiciona apenas a coluna products.image_url.
    O autogenerate detectou drift pré-existente (índices/FK/NULL de outras
    tabelas) não relacionado a esta feature; essas operações foram removidas de
    propósito para não ser destrutivo.
    """
    op.add_column('products', sa.Column('image_url', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('products', 'image_url')

"""recreate tokens table

Revision ID: 4c821097b713
Revises: 4e1ae93cfaa8
Create Date: 2026-02-19 10:02:18.235331

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c821097b713'
down_revision: Union[str, Sequence[str], None] = '4e1ae93cfaa8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('tokens')
    op.create_table('tokens',
    sa.Column('id', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )



def downgrade() -> None:
    """Downgrade schema."""
    pass

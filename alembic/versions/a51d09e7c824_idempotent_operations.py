"""Persist idempotent responses for offline creations."""
from alembic import op
import sqlalchemy as sa

revision = 'a51d09e7c824'
down_revision = 'f4c8a2d913ef'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('api_operations',
        sa.Column('key', sa.String(160), primary_key=True),
        sa.Column('request_hash', sa.String(64), nullable=False),
        sa.Column('response_json', sa.String(), nullable=False))

def downgrade():
    op.drop_table('api_operations')

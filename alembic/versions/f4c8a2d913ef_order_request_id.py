"""Deduplicate retries of offline sales."""
from alembic import op
import sqlalchemy as sa

revision = 'f4c8a2d913ef'
down_revision = 'e3b7a1c942d0'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('orders') as batch:
        batch.add_column(sa.Column('client_request_id', sa.String(100), nullable=True))
        batch.create_unique_constraint('uq_orders_client_request_id', ['client_request_id'])

def downgrade():
    with op.batch_alter_table('orders') as batch:
        batch.drop_constraint('uq_orders_client_request_id', type_='unique')
        batch.drop_column('client_request_id')

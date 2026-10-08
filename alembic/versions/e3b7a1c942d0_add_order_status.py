"""Preserve discount information while keeping the boolean payment status."""
from alembic import op
import sqlalchemy as sa
revision = 'e3b7a1c942d0'
down_revision = 'd2a6f90831ce'
branch_labels = None
depends_on = None

def upgrade():
    columns = sa.inspect(op.get_bind()).get_columns('orders')
    if not any(column['name'] == 'discount_value' for column in columns):
        op.add_column('orders', sa.Column('discount_value', sa.Float(), nullable=False, server_default=sa.text('0')))

def downgrade():
    with op.batch_alter_table('orders') as batch:
        batch.drop_column('discount_value')

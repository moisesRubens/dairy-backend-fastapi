"""Restore the deployed discount revision whose source file was missing.

The revision and parent were recovered from the existing migration bytecode.
"""
from alembic import op
import sqlalchemy as sa

revision = 'b1d6e9a42f31'
down_revision = 'ae778e8953d7'
branch_labels = None
depends_on = None

def upgrade():
    if not any(column['name'] == 'discount_value' for column in sa.inspect(op.get_bind()).get_columns('orders')):
        op.add_column('orders', sa.Column('discount_value', sa.Float(), nullable=False, server_default=sa.text('0')))

def downgrade():
    if any(column['name'] == 'discount_value' for column in sa.inspect(op.get_bind()).get_columns('orders')):
        with op.batch_alter_table('orders') as batch:
            batch.drop_column('discount_value')

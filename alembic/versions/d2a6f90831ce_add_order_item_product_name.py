"""Save the product name on each order item.

Revision ID: d2a6f90831ce
Revises: ae778e8953d7
"""
from alembic import op
import sqlalchemy as sa

revision = "d2a6f90831ce"
down_revision = "ae778e8953d7"
branch_labels = None
depends_on = None


def upgrade():
    columns = sa.inspect(op.get_bind()).get_columns("item_order")
    if any(column["name"] == "product_name" for column in columns):
        return
    op.add_column("item_order", sa.Column("product_name", sa.String(100), nullable=True))
    op.execute(sa.text("""
        UPDATE item_order SET product_name = COALESCE(
            (SELECT name FROM products WHERE products.id = item_order.product_id),
            'Produto removido'
        )
    """))
    with op.batch_alter_table("item_order") as batch:
        batch.alter_column("product_name", existing_type=sa.String(100), nullable=False)


def downgrade():
    with op.batch_alter_table("item_order") as batch:
        batch.drop_column("product_name")

"""Restore the deployed item snapshot revision from its migration bytecode."""
from alembic import op
import sqlalchemy as sa

revision = 'b17d4a8c92ef'
down_revision = 'b1d6e9a42f31'
branch_labels = None
depends_on = None

def upgrade():
    columns = {column['name']: column for column in sa.inspect(op.get_bind()).get_columns('item_order')}
    if 'id' in columns and 'product_name' in columns and columns['product_id']['nullable']:
        return
    op.execute('''CREATE TABLE item_order_new (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER,
        product_name VARCHAR(100) NOT NULL,
        item_price FLOAT NOT NULL,
        amount INTEGER, kg FLOAT, liters FLOAT,
        FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
    )''')
    id_column = 'id, ' if 'id' in columns else ''
    id_value = 'io.id, ' if 'id' in columns else ''
    name_value = "COALESCE(io.product_name, p.name, 'Produto removido')" if 'product_name' in columns else "COALESCE(p.name, 'Produto removido')"
    op.execute(f'''INSERT INTO item_order_new
        ({id_column}order_id, product_id, product_name, item_price, amount, kg, liters)
        SELECT {id_value}io.order_id, CASE WHEN p.id IS NULL THEN NULL ELSE io.product_id END,
               {name_value}, io.item_price, io.amount, io.kg, io.liters
        FROM item_order AS io LEFT JOIN products AS p ON p.id = io.product_id''')
    op.drop_table('item_order')
    op.rename_table('item_order_new', 'item_order')

def downgrade():
    connection = op.get_bind()
    if connection.execute(sa.text('SELECT COUNT(*) FROM item_order WHERE product_id IS NULL')).scalar_one():
        raise RuntimeError('Cannot downgrade: historical items have no product_id')
    op.execute('''CREATE TABLE item_order_old (
        order_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
        item_price FLOAT NOT NULL, amount INTEGER, kg FLOAT, liters FLOAT,
        PRIMARY KEY(order_id, product_id),
        FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    )''')
    op.execute('''INSERT INTO item_order_old (order_id, product_id, item_price, amount, kg, liters)
        SELECT order_id, product_id, item_price, amount, kg, liters FROM item_order''')
    op.drop_table('item_order')
    op.rename_table('item_order_old', 'item_order')

"""Convert monetary columns from reais in Float to integer centavos."""
from decimal import Decimal, ROUND_HALF_UP
from alembic import op
import sqlalchemy as sa

revision = 'd8e4b029a751'
down_revision = 'c92e71a4d063'
branch_labels = None
depends_on = None

COLUMNS = {'products': ['price'], 'orders': ['total_value', 'discount_value'],
           'item_order': ['item_price'], 'retiradas_produto': ['total_value']}


def upgrade():
    connection = op.get_bind()
    # Validate every amount before touching any table.
    changes = []
    for table, names in COLUMNS.items():
        columns = {c['name']: c for c in sa.inspect(connection).get_columns(table)}
        pending = [name for name in names if not isinstance(columns[name]['type'], sa.Integer)]
        if not pending:
            continue
        rows = connection.execute(sa.text(f'SELECT rowid, {", ".join(pending)} FROM {table}')).all()
        converted = []
        for row in rows:
            values = {'row_id': row[0]}
            for name, raw in zip(pending, row[1:]):
                if raw is None:
                    values[name] = None
                    continue
                amount = Decimal(str(raw))
                if not amount.is_finite() or abs(amount) > Decimal('999999999999.99'):
                    raise ValueError(f'Invalid monetary amount in {table}.{name}, row {row[0]}')
                values[name] = int(amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) * 100)
            converted.append(values)
        changes.append((table, pending, columns, converted))
    for table, pending, columns, converted in changes:
        if converted:
            assignments = ', '.join(f'{name} = :{name}' for name in pending)
            connection.execute(sa.text(f'UPDATE {table} SET {assignments} WHERE rowid = :row_id'), converted)
        with op.batch_alter_table(table) as batch:
            for name in pending:
                batch.alter_column(name, existing_type=columns[name]['type'], type_=sa.BigInteger(),
                                   existing_nullable=columns[name]['nullable'])


def downgrade():
    raise RuntimeError('Money migration requires a backup restore to downgrade without precision loss')

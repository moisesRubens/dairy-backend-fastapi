import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

path = Path(__file__).resolve().parents[1] / 'alembic/versions/e3b7a1c942d0_add_order_status.py'
spec = importlib.util.spec_from_file_location('order_status_migration', path)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)

class OrderStatusMigrationTests(unittest.TestCase):
    def test_adds_discount_column_and_preserves_existing_orders(self):
        engine = create_engine('sqlite://')
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql('CREATE TABLE orders (id INTEGER PRIMARY KEY, status BOOLEAN, total_value FLOAT)')
                connection.exec_driver_sql('INSERT INTO orders VALUES (1, 1, 10), (2, 0, 20)')
                with patch.object(migration, 'op', Operations(MigrationContext.configure(connection))):
                    migration.upgrade()
                    migration.upgrade()
                self.assertEqual(list(connection.exec_driver_sql('SELECT status, total_value, discount_value FROM orders ORDER BY id')), [(1, 10, 0), (0, 20, 0)])
                self.assertIn('discount_value', [c['name'] for c in inspect(connection).get_columns('orders')])
        finally:
            engine.dispose()

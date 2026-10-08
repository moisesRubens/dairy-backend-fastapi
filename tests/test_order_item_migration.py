"""Migration test on an isolated legacy SQLite schema."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

path = Path(__file__).resolve().parents[1] / "alembic/versions/d2a6f90831ce_add_order_item_product_name.py"
spec = importlib.util.spec_from_file_location("order_item_migration", path)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


class OrderItemMigrationTests(unittest.TestCase):
    def test_upgrade_backfills_names_preserves_items_and_is_repeatable(self):
        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("CREATE TABLE products (id INTEGER PRIMARY KEY, name VARCHAR(100))")
                connection.exec_driver_sql("""CREATE TABLE item_order (
                    order_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
                    item_price FLOAT NOT NULL, kg FLOAT,
                    PRIMARY KEY(order_id, product_id))""")
                connection.exec_driver_sql("INSERT INTO products VALUES (2, 'Queijo')")
                connection.exec_driver_sql("INSERT INTO item_order VALUES (1, 2, 42, 2)")
                with patch.object(migration, "op", Operations(MigrationContext.configure(connection))):
                    migration.upgrade()
                    migration.upgrade()
                row = connection.exec_driver_sql("SELECT product_name, item_price, kg FROM item_order").one()
                self.assertEqual(tuple(row), ("Queijo", 42, 2))
                column = next(c for c in inspect(connection).get_columns("item_order") if c["name"] == "product_name")
                self.assertFalse(column["nullable"])
        finally:
            engine.dispose()

import importlib.util
import sys
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database.money import money, subtotal, ensure_money_schema
from database.model import Base, Product, Order, RetiradaProduto, SalePoints
from controllers.product_controller import product_router
from controllers.sale_point_controller import sale_point_router
from controllers.order_controller import order_router
from dependencies.dependencies import make_session
from dependencies.sale_point_dependencies import validate_token
from schemas.product_schema import ProductRequestDTO
from services.idempotency import fingerprint


class MoneyTests(unittest.TestCase):
    def test_half_up_and_exact_arithmetic(self):
        self.assertEqual(money('1.005'), Decimal('1.01'))
        self.assertEqual(money('0.10') + money('0.20'), Decimal('0.30'))
        self.assertEqual(subtotal('0.10', 0.05), Decimal('0.01'))
        for value in (True, 'NaN', 'Infinity', 'abc', '1000000000000'):
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                money(value)

    def test_requests_use_decimal_and_keep_legacy_idempotency_hash(self):
        dto = ProductRequestDTO(name='Leite', price='1.005', liters=1)
        self.assertEqual(dto.price, Decimal('1.01'))
        self.assertEqual(dto.model_dump(mode='json')['price'], 1.01)
        self.assertEqual(fingerprint({'price': Decimal('1.10')}), fingerprint({'price': 1.1}))

    def test_http_items_round_before_sum_discount_and_sql_storage(self):
        engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        sessions = sessionmaker(bind=engine)
        app = FastAPI()
        for router in (product_router, sale_point_router, order_router):
            app.include_router(router)
        def dependency():
            with sessions() as session:
                yield session
        app.dependency_overrides[make_session] = dependency
        app.dependency_overrides[validate_token] = lambda: {'sub': '1'}
        try:
            with sessions() as session:
                session.add(SalePoints(id=1, name='Centro', password='hash', level=1))
                session.commit()
            with TestClient(app) as client:
                products = client.post('/products', json=[
                    {'name': 'A', 'price': '0.10', 'liters': 1},
                    {'name': 'B', 'price': '0.10', 'liters': 1},
                ])
                self.assertEqual(products.status_code, 201, products.text)
                ids = [p['id'] for p in products.json()]
                with sessions() as session:
                    session.add_all([RetiradaProduto(sale_point_id=1, product_id=id,
                        taken_quantity=1, remaining_quantity=1, sold_quantity=0,
                        total_value=0, unidade='liters', data=datetime.now()) for id in ids])
                    session.commit()
                payload = {'client_request_id': 'cents-retry', 'order_status': 'desconto',
                    'total_value': '0.01', 'items': [{'product_id': id, 'quantity': 0.05} for id in ids]}
                created = client.post('/sale-points/1/orders', json=payload)
                self.assertEqual(created.status_code, 201, created.text)
                self.assertEqual(created.json()['total_value'], 0.01)
                retry = client.post('/sale-points/1/orders', json=payload)
                self.assertEqual(retry.json(), created.json())
                with sessions() as session:
                    order = session.get(Order, created.json()['id'])
                    self.assertEqual(order.discount_value, Decimal('0.01'))
                    self.assertEqual(session.query(Order).count(), 1)
                    self.assertEqual(session.query(func.sum(Order.total_value)).scalar(), Decimal('0.01'))
                    self.assertEqual(session.execute(text('SELECT total_value, discount_value, typeof(total_value) FROM orders')).one(), (1, 1, 'integer'))
                    self.assertEqual(session.execute(text('SELECT price FROM products ORDER BY id')).scalars().all(), [10, 10])
                    self.assertEqual(session.query(RetiradaProduto).first().total_value, Decimal('0.01'))
                patched = client.patch(f"/orders/{created.json()['id']}", json={'order_status': 'pago'})
                self.assertEqual(patched.status_code, 200, patched.text)
                self.assertEqual(patched.json()['total_value'], 0.02)
        finally:
            engine.dispose()


class MoneyMigrationTests(unittest.TestCase):
    def test_legacy_amounts_become_cents_and_repeat_is_safe(self):
        path = Path(__file__).resolve().parents[1] / 'alembic/versions/d8e4b029a751_money_in_integer_cents.py'
        spec = importlib.util.spec_from_file_location('money_migration', path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        engine = create_engine('sqlite://')
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql('CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT UNIQUE, price FLOAT)')
                connection.exec_driver_sql('CREATE TABLE orders (id INTEGER PRIMARY KEY, total_value FLOAT NOT NULL, discount_value FLOAT NOT NULL DEFAULT 0)')
                connection.exec_driver_sql('CREATE TABLE item_order (id INTEGER PRIMARY KEY, product_id INTEGER REFERENCES products(id), item_price FLOAT NOT NULL, kg FLOAT)')
                connection.exec_driver_sql('CREATE TABLE retiradas_produto (id INTEGER PRIMARY KEY, total_value FLOAT NOT NULL, remaining_quantity FLOAT)')
                connection.exec_driver_sql("INSERT INTO products VALUES (1, 'A', 1.005), (2, 'B', NULL)")
                connection.exec_driver_sql('INSERT INTO orders VALUES (1, 0.30000000000000004, 0.005)')
                connection.exec_driver_sql('INSERT INTO item_order VALUES (1, 1, 1.005, 0.05)')
                connection.exec_driver_sql('INSERT INTO retiradas_produto VALUES (1, 0.3, 0.95)')
                with self.assertRaisesRegex(RuntimeError, 'requires migration'):
                    ensure_money_schema(connection)
                with patch.object(migration, 'op', Operations(MigrationContext.configure(connection))):
                    migration.upgrade()
                    migration.upgrade()
                self.assertEqual(connection.exec_driver_sql('SELECT price FROM products ORDER BY id').scalars().all(), [101, None])
                self.assertEqual(connection.exec_driver_sql('SELECT total_value, discount_value, typeof(total_value) FROM orders').one(), (30, 1, 'integer'))
                self.assertEqual(connection.exec_driver_sql('SELECT item_price, kg FROM item_order').one(), (101, 0.05))
                self.assertEqual(connection.exec_driver_sql('SELECT total_value, remaining_quantity FROM retiradas_produto').one(), (30, 0.95))
                self.assertTrue(inspect(connection).get_foreign_keys('item_order'))
                ensure_money_schema(connection)
        finally:
            engine.dispose()

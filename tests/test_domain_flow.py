import unittest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from dependencies.dependencies import make_session
from exceptions.common_exceptions import AdminPermissionRequired
from database.model import Base, Product, SalePoints, Order, ItemsOrder, OrderSalePoint, RetiradaProduto
from services.product_service import delete_all_products_service
from dependencies.sale_point_dependencies import validate_token


class DomainFlowIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)

        @event.listens_for(self.engine, 'connect')
        def enable_foreign_keys(connection, record):
            connection.execute('PRAGMA foreign_keys=ON')

        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        self.overrides = app.dependency_overrides.copy()

        def dependency():
            with self.sessions() as session:
                yield session

        app.dependency_overrides[make_session] = dependency
        app.dependency_overrides[validate_token] = lambda: {'sub': '1', 'level': 1}
        self.client = TestClient(app, raise_server_exceptions=False)
        with self.sessions() as session:
            session.add_all([SalePoints(id=1, name='Admin', password='hash', level=1),
                             SalePoints(id=2, name='Seller', password='hash', level=0)])
            session.flush()
            session.add_all([Product(id=1, name='Leite', price=5, liters=10),
                             Order(id=1, status=False, total_value=5, order_date=datetime(2026, 10, 6))])
            session.flush()
            session.add_all([OrderSalePoint(order_id=1, sale_point_id=2),
                             ItemsOrder(order_id=1, product_id=1, product_name='Leite', item_price=5, liters=1),
                             RetiradaProduto(id=1, sale_point_id=2, product_id=1, unidade='liters',
                                             taken_quantity=2, remaining_quantity=2, sold_quantity=0)])
            session.commit()

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.overrides)
        self.engine.dispose()

    def test_non_admin_delete_is_403_in_all_domains_and_preserves_data(self):
        with self.sessions() as session:
            session.get(SalePoints, 1).level = 0
            session.commit()
        for path in ('/products/1', '/products', '/sale-points/2', '/sale-points',
                     '/orders/1', '/orders', '/sale-points/2/orders', '/sale-points/2/outbounds'):
            with self.subTest(path=path), self.assertLogs('dairy.main', level='WARNING') as logs:
                response = self.client.delete(path)
                self.assertEqual(response.status_code, 403, response.text)
                self.assertIn('Somente administradores', response.json()['detail'])
                self.assertIn('AdminPermissionRequired', logs.output[0])
        with self.sessions() as session:
            self.assertEqual(session.query(Product).count(), 1)
            self.assertEqual(session.query(Order).count(), 1)
            self.assertTrue(session.get(RetiradaProduto, 1).status)

    def test_product_delete_returns_snapshot_and_preserves_sale_history(self):
        expected = self.client.get('/products/1').json()
        response = self.client.delete('/products/1')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), expected)
        with self.sessions() as session:
            self.assertIsNone(session.get(Product, 1))
            item = session.query(ItemsOrder).one()
            self.assertIsNone(item.product_id)
            self.assertEqual(item.product_name, 'Leite')
            self.assertIsNotNone(session.get(Order, 1))
        with self.assertLogs('dairy.main', level='WARNING'):
            self.assertEqual(self.client.delete('/products/1').status_code, 404)

    def test_product_bulk_delete_returns_list_then_empty_list(self):
        response = self.client.delete('/products')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual([item['id'] for item in response.json()], [1])
        response = self.client.delete('/products')
        self.assertEqual((response.status_code, response.json()), (200, []))

    def test_sale_point_delete_returns_snapshot_without_password(self):
        response = self.client.delete('/sale-points/2')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['id'], 2)
        self.assertNotIn('password', response.json())
        with self.sessions() as session:
            self.assertIsNone(session.get(SalePoints, 2))
            self.assertIsNotNone(session.get(Order, 1))
            self.assertIsNotNone(session.get(Product, 1))

    def test_nested_order_delete_returns_deleted_orders(self):
        response = self.client.delete('/sale-points/2/orders')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual([item['id'] for item in response.json()['orders']], [1])
        with self.sessions() as session:
            self.assertEqual(session.query(Order).count(), 0)
            self.assertEqual(session.query(ItemsOrder).count(), 0)

    def test_admin_outbound_delete_closes_and_returns_stock_without_erasing_history(self):
        response = self.client.delete('/sale-points/2/outbounds')
        self.assertEqual(response.status_code, 200, response.text)
        with self.sessions() as session:
            self.assertFalse(session.get(RetiradaProduto, 1).status)
            self.assertEqual(session.get(Product, 1).liters, 12)

    def test_unexpected_errors_reach_handler_without_exposing_details(self):
        for path, target in (
            ('/products/1', 'controllers.product_controller.get_product_service'),
            ('/outbounds/1', 'controllers.outbound_controller.get_outbound_service'),
            ('/sale-points/2', 'controllers.sale_point_controller.get_sale_point_service'),
        ):
            with self.subTest(path=path), patch(target, side_effect=RuntimeError('private SQL password')):
                with self.assertLogs('dairy.main', level='WARNING') as logs:
                    response = self.client.get(path)
                self.assertEqual(response.status_code, 500)
                self.assertEqual(response.json(), {'detail': 'Erro interno do servidor'})
                self.assertIn('private SQL password', logs.output[0])
                self.assertIsNotNone(logs.records[0].exc_info)

    def test_service_raises_domain_permission_exception(self):
        with self.sessions() as session:
            with self.assertRaises(AdminPermissionRequired):
                delete_all_products_service(session, {'sub': '2'})
            self.assertFalse(session.in_transaction())
            self.assertIsNotNone(session.get(Product, 1))

    def test_product_bulk_delete_rolls_back_sql_changes_on_failure(self):
        with self.sessions() as session:
            original_flush = session.flush

            def fail_after_delete(*args, **kwargs):
                original_flush(*args, **kwargs)
                if session.query(Product).count() == 0:
                    raise RuntimeError('failure after deleting products')

            # Fail after SQL is emitted during commit, then verify rollback restores it.
            with patch.object(session, 'flush', side_effect=fail_after_delete):
                with self.assertRaises(RuntimeError):
                    delete_all_products_service(session, {'sub': '1'})
            self.assertFalse(session.in_transaction())
            self.assertIsNotNone(session.get(Product, 1))
            self.assertEqual(session.query(ItemsOrder).one().product_id, 1)

    def test_real_authentication_queries_do_not_conflict_with_write_transaction(self):
        app.dependency_overrides.pop(validate_token)
        with patch('dependencies.sale_point_dependencies.decode', return_value={'sub': '1'}), \
             patch('dependencies.sale_point_dependencies.config', return_value='unused'):
            response = self.client.delete('/products/1', headers={'Authorization': 'Bearer token'})
        self.assertEqual(response.status_code, 200, response.text)

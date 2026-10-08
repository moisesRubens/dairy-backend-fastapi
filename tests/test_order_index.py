import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))

from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from dependencies.dependencies import make_session
from database.model import Base, Order, OrderSalePoint, SalePoints
from dependencies.sale_point_dependencies import validate_token


class OrderIndexIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            'sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        self.previous_overrides = app.dependency_overrides.copy()

        def session_dependency():
            with self.sessions() as session:
                yield session

        app.dependency_overrides[make_session] = session_dependency
        app.dependency_overrides[validate_token] = lambda: {'sub': '1'}
        self.client = TestClient(app)
        with self.sessions() as session:
            session.add(SalePoints(id=1, name='Centro', password='hash', level=0))
            session.commit()

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.previous_overrides)
        self.engine.dispose()

    def add_order(self, description='Queijo', status=False, day=datetime(2026, 10, 6)):
        with self.sessions() as session:
            order = Order(description=description, status=status, total_value=10, order_date=day)
            session.add(order)
            session.flush()
            session.add(OrderSalePoint(order_id=order.id, sale_point_id=1))
            session.commit()
            return order.id

    def test_empty_collection_returns_200_and_empty_list(self):
        response = self.client.get('/orders')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_default_page_size_and_ordering(self):
        ids = [self.add_order() for _ in range(23)]
        response = self.client.get('/orders')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual([order['id'] for order in response.json()], ids[:20])
        self.assertIn('date', response.json()[0])
        self.assertNotIn('order_date', response.json()[0])

    def test_filters_are_applied_before_pagination(self):
        self.add_order(status=True)
        self.add_order(description='Leite')
        self.add_order(day=datetime(2026, 10, 5))
        ids = [self.add_order(description='Venda QUEIJO') for _ in range(5)]
        params = dict(date='2026-10-06', description='queijo', status='false', size=2)
        for page, expected in [(1, ids[:2]), (2, ids[2:4]), (3, ids[4:]), (4, [])]:
            with self.subTest(page=page):
                response = self.client.get('/orders', params={**params, 'page': page})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual([order['id'] for order in response.json()], expected)

    def test_unmatched_filter_returns_empty_list(self):
        self.add_order()
        response = self.client.get('/orders?description=inexistente')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_invalid_input_uses_global_handler_before_service(self):
        for field, value in [('page', 'abc'), ('page', '0'), ('size', '0'),
                             ('size', '-1'), ('size', '1.5'), ('date', 'invalid'),
                             ('status', 'invalid')]:
            with self.subTest(field=field, value=value):
                with patch('controllers.order_controller.list_orders_service') as service:
                    with self.assertLogs('dairy.main', level='WARNING'):
                        response = self.client.get('/orders', params={field: value})
                    service.assert_not_called()
                self.assertEqual(response.status_code, 422)
                error = response.json()['detail'][0]
                self.assertEqual(error['loc'], ['query', field])
                self.assertIn('msg', error)
                self.assertIn('type', error)

    def test_service_failure_returns_500_and_logs_traceback(self):
        with patch('controllers.order_controller.list_orders_service', side_effect=RuntimeError('Falha no banco')):
            with self.assertLogs('dairy.main', level='WARNING') as logs:
                with TestClient(app, raise_server_exceptions=False) as client:
                    response = client.get('/orders')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {'detail': 'Erro interno do servidor'})
        self.assertIn('Falha no banco', logs.output[0])
        self.assertIsNotNone(logs.records[0].exc_info)

    def test_authentication_is_required(self):
        app.dependency_overrides.pop(validate_token)
        response = self.client.get('/orders')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers['www-authenticate'], 'Bearer')

    def test_http_exception_preserves_status_message_and_headers(self):
        error = HTTPException(403, 'Sem permissao', headers={'X-Error': 'permission'})
        with patch('controllers.order_controller.list_orders_service', side_effect=error):
            with self.assertLogs('dairy.main', level='WARNING'):
                response = self.client.get('/orders')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {'detail': 'Sem permissao'})
        self.assertEqual(response.headers['x-error'], 'permission')


if __name__ == '__main__':
    unittest.main()

import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from dependencies.dependencies import make_session
from database.model import Base, Order, OrderSalePoint, SalePoints
from dependencies.sale_point_dependencies import validate_token


class OrderIntegrationFixture:
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
            session.flush()
            order = Order(
                description='Queijo', status=False, total_value=10,
                order_date=datetime(2026, 10, 6),
            )
            session.add(order)
            session.flush()
            self.order_id = order.id
            session.add(OrderSalePoint(order_id=order.id, sale_point_id=1))
            session.commit()

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.previous_overrides)
        self.engine.dispose()

class OrderShowIntegrationTests(OrderIntegrationFixture, unittest.TestCase):
    def test_existing_order_returns_200_and_order_data(self):
        response = self.client.get(f'/orders/{self.order_id}')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {
            'id': self.order_id,
            'status': False,
            'order_status': 'pendente',
            'total_value': 10.0,
            'description': 'Queijo',
            'date': '2026-10-06T00:00:00',
            'sale_point_id': 1,
            'item_order': [],
        })

    def test_missing_order_returns_404_and_logs_original_exception(self):
        with self.assertLogs('dairy.main', level='WARNING') as logs:
            response = self.client.get(f'/orders/{self.order_id + 1}')
        self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(response.json(), {'detail': 'Pedido não encontrado'})
        self.assertIn('Pedido não encontrado', logs.output[0])
        self.assertIsNotNone(logs.records[0].exc_info)


if __name__ == '__main__':
    unittest.main()

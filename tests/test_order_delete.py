import unittest
from unittest.mock import patch

from test_order_show import OrderIntegrationFixture
from database.model import Order, OrderSalePoint, SalePoints
from services.order_service import delete_order


class OrderDeleteIntegrationTests(OrderIntegrationFixture, unittest.TestCase):
    def set_admin(self, level=1):
        with self.sessions() as session:
            session.get(SalePoints, 1).level = level
            session.commit()

    def test_admin_delete_returns_snapshot_and_removes_order_and_links(self):
        self.set_admin()
        expected = self.client.get(f'/orders/{self.order_id}').json()
        response = self.client.delete(f'/orders/{self.order_id}')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), expected)
        with self.sessions() as session:
            self.assertIsNone(session.get(Order, self.order_id))
            self.assertEqual(session.query(OrderSalePoint).count(), 0)

    def test_admin_delete_all_returns_list_and_empty_list_on_repeat(self):
        self.set_admin()
        expected = self.client.get(f'/orders/{self.order_id}').json()
        response = self.client.delete('/orders')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), [expected])
        with self.sessions() as session:
            self.assertEqual(session.query(Order).count(), 0)
            self.assertEqual(session.query(OrderSalePoint).count(), 0)
        response = self.client.delete('/orders')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_non_admin_cannot_delete_even_with_admin_claim(self):
        from main import app
        from dependencies.sale_point_dependencies import validate_token
        app.dependency_overrides[validate_token] = lambda: {'sub': '1', 'level': 1}
        for level in (0, 2, None):
            self.set_admin(level)
            for path in (f'/orders/{self.order_id}', '/orders'):
                with self.subTest(level=level, path=path):
                    with self.assertLogs('dairy.main', level='WARNING'):
                        response = self.client.delete(path)
                    self.assertEqual(response.status_code, 403, response.text)
                    with self.sessions() as session:
                        self.assertIsNotNone(session.get(Order, self.order_id))

    def test_admin_missing_order_returns_404(self):
        self.set_admin()
        with self.assertLogs('dairy.main', level='WARNING'):
            response = self.client.delete(f'/orders/{self.order_id + 1}')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'Pedido não encontrado'})

    def test_delete_failure_rolls_back_and_keeps_session_open(self):
        self.set_admin()
        with self.sessions() as session:
            original_flush = session.flush

            def failing_flush(*args, **kwargs):
                original_flush(*args, **kwargs)
                raise RuntimeError('Failure after SQL deletion')

            with patch.object(session, 'flush', side_effect=failing_flush):
                with self.assertRaises(RuntimeError):
                    delete_order(self.order_id, session, {'sub': '1'})
            self.assertFalse(session.in_transaction())
            self.assertIsNotNone(session.get(Order, self.order_id))

import unittest
from datetime import datetime
import test_resource_rest as fixtures
from database.model import SalePoints, Product, Order, ItemsOrder, OrderSalePoint, RetiradaProduto


class DailyProfileSalesTests(unittest.TestCase):
    setUp = fixtures.ResourceIntegrationTests.setUp
    tearDown = fixtures.ResourceIntegrationTests.tearDown

    def seed(self):
        with self.sessions() as session:
            session.add_all([SalePoints(id=2, name='Bairro', password='hash'),
                             SalePoints(id=3, name='Sem vendas', password='hash')])
            product = Product(name='Leite', price=5, liters=100)
            session.add(product)
            session.flush()
            for point, when, total, paid, discount in [
                (1, datetime(2026, 10, 2, 23, 59), 900, True, 0),
                (1, datetime(2026, 10, 3, 0, 0), 20, True, 5),
                (1, datetime(2026, 10, 3, 23, 59), 10, False, 0),
                (1, datetime(2026, 10, 4, 0, 0), 800, True, 0),
                (2, datetime(2026, 10, 3, 12), 45, True, 0),
            ]:
                order = Order(order_date=when, total_value=total, status=paid, discount_value=discount)
                session.add(order)
                session.flush()
                session.add(OrderSalePoint(order_id=order.id, sale_point_id=point))
                # Multiple items must not multiply the order total.
                for value in ((total + discount) / 2, (total + discount) / 2):
                    session.add(ItemsOrder(order_id=order.id, product_id=product.id,
                                           product_name='Leite', item_price=5, liters=value / 5))
            for point, day, total, sold, active in [(1, 2, 900, 180, True), (1, 3, 35, 7, False), (2, 3, 45, 9, True)]:
                session.add(RetiradaProduto(sale_point_id=point, product_id=product.id,
                    data=datetime(2026, 10, day), unidade='liters', taken_quantity=200,
                    sold_quantity=sold, remaining_quantity=200-sold, total_value=total, status=active))
            session.commit()

    def test_profiles_match_daily_orders_with_discount_pending_and_date_boundaries(self):
        self.seed()
        response = self.client.get('/outbounds?date=2026-10-03')
        self.assertEqual(response.status_code, 200, response.text)
        profiles = {row['sale_point_id']: row for row in response.json()}
        self.assertEqual(profiles[1]['sales_total'], 30)
        self.assertEqual(profiles[2]['sales_total'], 45)
        self.assertEqual(profiles[3]['sales_total'], 0)
        self.assertEqual(len(profiles[1]['outbounds']), 1)
        self.assertEqual(profiles[1]['outbounds'][0]['sold_quantity'], 7)
        self.assertFalse(profiles[1]['outbounds'][0]['status'])
        for point in profiles:
            orders = self.client.get(f'/sale-points/{point}/orders?date=2026-10-03&include_pending=true')
            self.assertEqual(orders.status_code, 200, orders.text)
            self.assertEqual(profiles[point]['sales_total'], sum(order['total_value'] for order in orders.json()))

    def test_empty_day_has_zero_sales_and_no_outbounds_for_each_point(self):
        self.seed()
        response = self.client.get('/outbounds?date=2026-10-05')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)
        for row in response.json():
            self.assertEqual(row['sales_total'], 0)
            self.assertEqual(row['outbounds'], [])

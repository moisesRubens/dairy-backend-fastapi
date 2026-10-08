from request_helpers import request_input
"""Contrato REST: testes unitarios e integracao com SQLite em memoria."""
import sys
import unittest
from datetime import datetime, date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database.model import Base, Product, SalePoints, RetiradaProduto, Order, ItemsOrder, OrderSalePoint
from dependencies.dependencies import make_session
from dependencies.sale_point_dependencies import validate_token
from controllers.sale_point_controller import sale_point_router
from controllers.order_controller import order_router
from controllers.product_controller import product_router
from controllers.outbound_controller import outbound_router
from controllers.order_controller import show, edit, delete
from exceptions.order_exceptions import OrderNotFoundException
from schemas.order_schema import ItemOrderRequestDTO, OrderUpdateDTO, OrderRequestDTO
from controllers.product_controller import get_product_controller, edit_product_controller
from schemas.product_schema import ProductRequestDTO, ProductUpdateDTO
from exceptions.product_exceptions import ProductNotFound, ExistingProductException, InsuficientProductsAmountException
from services.product_service import validate_product, create_product_service
from schemas.outbound_schema import OutboundRequestDTO
from controllers.outbound_controller import edit_outbound_controller
from exceptions.outbound_exceptions import OutboundNotFound


def migrate_money_schema(connection):
    import importlib.util
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    path = Path(__file__).resolve().parents[1] / 'alembic/versions/d8e4b029a751_money_in_integer_cents.py'
    spec = importlib.util.spec_from_file_location('legacy_money_migration', path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with patch.object(migration, 'op', Operations(MigrationContext.configure(connection))):
        migration.upgrade()


class ResourceUnitTests(unittest.IsolatedAsyncioTestCase):
    async def test_order_status_and_final_value_validation(self):
        for status in ('pago', 'pendente', 'desconto'):
            dto = OrderRequestDTO(order_status=status, total_value=7.5, items=[{'product_id': 1, 'quantity': 2}])
            self.assertEqual(dto.order_status, status)
        for payload in ({'order_status': 'invalido'}, {'total_value': 0}, {'total_value': -1}, {'total_value': float('inf')}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                OrderRequestDTO(items=[{'product_id': 1, 'quantity': 2}], **payload)

    async def test_order_item_name_uses_saved_snapshot_without_product_relationship(self):
        item = ItemsOrder(product_name="Queijo", product_id=2, order_id=1, item_price=42, kg=2)
        self.assertEqual(item.name, "Queijo")

    async def test_order_controllers_call_sync_services_and_map_missing_to_404(self):
        session = object()
        with patch("controllers.order_controller.search_order", return_value={"id": 7}) as service:
            self.assertEqual(show(7, session=session, user={}), {"id": 7})
            service.assert_called_once_with(session, {}, 7)
        with patch("controllers.order_controller.search_order", side_effect=OrderNotFoundException()):
            with self.assertRaises(HTTPException) as caught:
                show(7, session=session, user={})
            self.assertEqual(caught.exception.status_code, 404)
        for name, invoke in [
            ("edit_order", lambda: edit(7, request_input(payload={'status': False}), session=session, user={})),
            ("delete_order", lambda: delete(7, session=session, user={})),
        ]:
            with patch("controllers.order_controller." + name, side_effect=OrderNotFoundException()):
                with self.assertRaises(HTTPException) as caught:
                    await invoke()
                self.assertEqual(caught.exception.status_code, 404)

    async def test_product_controllers_map_missing_and_conflict(self):
        for name, error, code, invoke in [
            ("get_product_service", ProductNotFound(), 404, lambda: get_product_controller(request_input(), session=None, user={})),
            ("edit_product_service", ProductNotFound(), 404, lambda: edit_product_controller(request_input(payload={'price': 0}), session=None, user={})),
            ("edit_product_service", ExistingProductException(), 409, lambda: edit_product_controller(request_input(payload={'name': 'Leite'}), session=None, user={})),
        ]:
            with patch("controllers.product_controller." + name, side_effect=error):
                with self.assertRaises(HTTPException) as result:
                    await invoke()
                self.assertEqual(result.exception.status_code, code)

    async def test_outbound_errors_keep_status_codes(self):
        for error, code in [(OutboundNotFound(), 404), (ProductNotFound(), 404), (InsuficientProductsAmountException(), 409), (HTTPException(422, "bad unit"), 422)]:
            with patch("controllers.outbound_controller.edit_outbound_service", side_effect=error):
                with self.assertRaises(HTTPException) as result:
                    await edit_outbound_controller(request_input(payload={'remaining_quantity': 0}), session=None, user={})
                self.assertEqual(result.exception.status_code, code)

    async def test_unit_validation_counts_zero_as_valid_and_rejects_multiple_units(self):
        self.assertTrue(validate_product(0, None, -1))
        self.assertFalse(validate_product(None, None, None))
        self.assertFalse(validate_product(0, 0, None))
        self.assertIsNone(ProductRequestDTO(name="Leite", price=0, liters=0, kg=-1).kg)
        for data in [{"liters": -0.5}, {"liters": 1, "kg": 1}, {}]:
            with self.assertRaises(ValueError):
                ProductRequestDTO(name="Leite", price=5, **data)
        for data in [{"quantity": 0}, {"quantity": 1, "liters": 1}, {}]:
            with self.assertRaises(ValueError):
                ItemOrderRequestDTO(product_id=1, **data)

    async def test_product_batch_rolls_back_conflict(self):
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = Product(id=1)
        with self.assertRaises(ExistingProductException):
            create_product_service([ProductRequestDTO(name="Leite", price=5, liters=2)], session)
        session.begin.return_value.__exit__.assert_called_once()
        session.commit.assert_not_called()


class ResourceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        app = FastAPI()
        for router in (sale_point_router, order_router, product_router, outbound_router):
            app.include_router(router)
        def dependency():
            with self.sessions() as session:
                yield session
        app.dependency_overrides[make_session] = dependency
        app.dependency_overrides[validate_token] = lambda: {"sub": "1"}
        self.app = app
        self.client = TestClient(app)
        with self.sessions() as session:
            session.add(SalePoints(id=1, name="Centro", password="hash", level=1))
            session.commit()

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def product(self, unit="liters", quantity=10, name="Leite"):
        response = self.client.post("/products", json=[{"name": name, "price": 5, unit: quantity}])
        self.assertEqual(response.status_code, 201, response.text)
        self.assertIsInstance(response.json()[0], dict)
        return response.json()[0]["id"]

    def outbound(self, unit="liters", product_id=None, remaining=4, sold=1):
        product_id = product_id or self.product(unit)
        with self.sessions() as session:
            outbound = RetiradaProduto(sale_point_id=1, product_id=product_id, taken_quantity=remaining+sold,
                                       remaining_quantity=remaining, sold_quantity=sold, unidade=unit,
                                       total_value=sold*5, status=True, data=datetime.now())
            session.add(outbound)
            session.commit()
            return outbound.id, product_id

    def order(self, description="Venda", status=True, day=datetime(2026, 10, 1, 10)):
        with self.sessions() as session:
            order = Order(description=description, status=status, total_value=5, order_date=day)
            session.add(order)
            session.flush()
            session.add(OrderSalePoint(order_id=order.id, sale_point_id=1))
            session.commit()
            return order.id

    def test_create_with_existing_not_null_discount_schema(self):
        # Reproduz a tabela real, em vez de depender apenas de create_all.
        with self.engine.begin() as connection:
            connection.exec_driver_sql('DROP TABLE orders')
            connection.exec_driver_sql("""CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status BOOLEAN NOT NULL,
                discount_value FLOAT NOT NULL,
                total_value FLOAT NOT NULL,
                description VARCHAR(200),
                client_request_id VARCHAR(100) UNIQUE,
                order_date DATETIME NOT NULL
            )""")
            migrate_money_schema(connection)
        for status in ('pago', 'pendente', 'desconto'):
            with self.subTest(status=status):
                product_id = self.product(name='Legado ' + status)
                self.outbound(product_id=product_id, remaining=4, sold=0)
                response = self.client.post('/sale-points/1/orders', json={
                    'order_status': status, 'total_value': 7.5,
                    'items': [{'product_id': product_id, 'quantity': 2}],
                })
                self.assertEqual(response.status_code, 201, response.text)
                self.assertEqual(response.json()['order_status'], status)
                with self.sessions() as session:
                    order = session.get(Order, response.json()['id'])
                    self.assertEqual(order.discount_value, 2.5 if status == 'desconto' else 0)
                patched = self.client.patch('/orders/' + str(response.json()['id']), json={'status': False})
                self.assertEqual(patched.status_code, 200, patched.text)
                self.assertEqual(patched.json()['order_status'], 'pendente')

    def test_create_order_status_and_discount_final_value_roundtrip(self):
        for status in ('pago', 'pendente', 'desconto'):
            with self.subTest(status=status):
                outbound_id, product_id = self.outbound('liters', remaining=4, sold=0,
                    product_id=self.product(name='Produto ' + status))
                response = self.client.post('/sale-points/1/orders', json={
                    'order_status': status, 'total_value': 7.5,
                    'items': [{'product_id': product_id, 'quantity': 2}],
                })
                self.assertEqual(response.status_code, 201, response.text)
                order = response.json()
                self.assertEqual(order['order_status'], status)
                self.assertEqual(order['status'], status != 'pendente')
                self.assertEqual(order['total_value'], 7.5 if status == 'desconto' else 10)
                listed = self.client.get('/sale-points/1/orders').json()
                self.assertEqual(next(o for o in listed if o['id'] == order['id'])['order_status'], status)
                with self.sessions() as session:
                    self.assertEqual(session.get(RetiradaProduto, outbound_id).remaining_quantity, 2)

    def test_invalid_discount_does_not_consume_stock_or_create_order(self):
        outbound_id, product_id = self.outbound(remaining=4, sold=0)
        for value in (None, 0, -1, 11):
            with self.subTest(value=value):
                response = self.client.post('/sale-points/1/orders', json={
                    'order_status': 'desconto', 'total_value': value,
                    'items': [{'product_id': product_id, 'quantity': 2}],
                })
                self.assertEqual(response.status_code, 422, response.text)
                self.assertEqual(self.client.get('/orders').json(), [])
                with self.sessions() as session:
                    self.assertEqual(session.get(RetiradaProduto, outbound_id).remaining_quantity, 4)

    def test_products_crud_and_partial_patch(self):
        self.assertEqual(self.client.get("/products").json(), [])
        id = self.product(quantity=0)
        before = self.client.get(f"/products/{id}").json()
        self.assertEqual(before["liters"], 0)
        edited = self.client.patch(f"/products/{id}", json={"price": 0})
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.json()["liters"], 0)
        self.assertEqual(edited.json()["price"], 0)
        self.assertEqual(self.client.patch(f"/products/{id}", json={"liters": None, "kg": 2}).status_code, 200)
        self.assertEqual(self.client.get(f"/products/{id}").json()["kg"], 2)
        response = self.client.delete(f"/products/{id}")
        self.assertEqual(response.status_code, 200, response.text)
        for method in ("get", "delete", "patch"):
            kwargs = {"json": {"price": 1}} if method == "patch" else {}
            self.assertEqual(getattr(self.client, method)(f"/products/{id}", **kwargs).status_code, 404)

    def test_products_invalid_units_conflicts_and_batch_atomicity(self):
        id = self.product()
        for payload in [[{"name": "Leite", "price": 5, "kg": 1}], [{"name": "Novo", "price": 5, "kg": 1}, {"name": "LEITE", "price": 5, "kg": 1}]]:
            self.assertEqual(self.client.post("/products", json=payload).status_code, 409)
        self.assertEqual(len(self.client.get("/products").json()), 1)
        self.assertEqual(self.client.post("/products", json=[]).status_code, 422)
        for payload in [{"liters": -1}, {"kg": 1}, {"price": -1}, {"name": " "}, {"unknown": 1}]:
            self.assertEqual(self.client.patch(f"/products/{id}", json=payload).status_code, 422)
        other = self.product(name="Queijo", unit="kg")
        self.assertEqual(self.client.patch(f"/products/{other}", json={"name": "LEITE"}).status_code, 409)
        self.assertEqual(self.client.patch(f"/products/{id}", json={"name": "LEITE"}).status_code, 200)
        self.assertEqual(self.client.delete("/products").status_code, 200)
        self.assertEqual(self.client.get("/products").json(), [])

    def test_orders_filters_metadata_patch_get_and_delete(self):
        id = self.order("Venda leite", False)
        self.order("Queijo", True, datetime(2026, 10, 2, 10))
        response = self.client.get("/orders", params={"date": "2026-10-01", "description": "leite", "status": "false"})
        self.assertEqual([o["id"] for o in response.json()], [id])
        self.assertEqual(self.client.get("/orders?status=true").json()[0]["description"], "Queijo")
        updated = self.client.patch(f"/orders/{id}", json={"description": None, "status": True, "order_date": "2026-10-03"})
        self.assertEqual(updated.status_code, 200)
        self.assertIsNone(updated.json()["description"])
        self.assertEqual(updated.json()["total_value"], 5)
        self.assertTrue(updated.json()["status"])
        self.assertEqual(self.client.get(f"/orders/{id}").json()["date"], "2026-10-03T00:00:00")
        self.assertEqual(self.client.get("/sale-points/1/orders?date=2026-10-03").json()[0]["id"], id)
        response = self.client.delete(f"/orders/{id}")
        self.assertEqual(response.status_code, 200, response.text)
        for method in ("get", "patch", "delete"):
            kwargs = {"json": {"status": False}} if method == "patch" else {}
            self.assertEqual(getattr(self.client, method)(f"/orders/{id}", **kwargs).status_code, 404)
        self.assertEqual(self.client.delete("/orders").status_code, 200)
        self.assertEqual(self.client.get("/orders").json(), [])

    def test_order_creation_quantity_contract_and_stock_transaction(self):
        outbound_id, product_id = self.outbound(remaining=4, sold=0)
        response = self.client.post("/sale-points/1/orders", json={"description": "Venda", "items": [{"product_id": product_id, "quantity": 2.5}]})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["total_value"], 12.5)
        self.assertEqual(response.headers["Location"], f"/orders/{response.json()['id']}")
        self.assertEqual(response.json()["item_order"][0]["liters"], 2.5)
        with self.sessions() as session:
            outbound = session.get(RetiradaProduto, outbound_id)
            self.assertEqual((outbound.remaining_quantity, outbound.sold_quantity, outbound.total_value), (1.5, 2.5, 12.5))
        response = self.client.post("/sale-points/1/orders", json={"items": [{"product_id": product_id, "quantity": 2}]})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(len(self.client.get("/orders").json()), 1)
        with self.sessions() as session:
            self.assertEqual(session.get(RetiradaProduto, outbound_id).remaining_quantity, 1.5)

    def test_order_creation_with_existing_database_item_schema(self):
        # O banco encontrado no projeto tem id e product_name obrigatorio,
        # diferentemente do modelo usado originalmente por create_all.
        with self.engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE item_order")
            connection.exec_driver_sql("""CREATE TABLE item_order (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES orders(id),
                product_id INTEGER REFERENCES products(id),
                product_name VARCHAR(100) NOT NULL,
                item_price FLOAT NOT NULL,
                amount INTEGER, kg FLOAT, liters FLOAT
            )""")
            migrate_money_schema(connection)
        product = self.product("kg", name="Queijo")
        with self.sessions() as session:
            session.get(Product, product).price = 42
            session.commit()
        outbound_id, _ = self.outbound("kg", product, remaining=3, sold=0)
        with self.sessions() as session:
            session.get(RetiradaProduto, outbound_id).data = datetime(2026, 10, 1, 10)
            session.commit()
        response = self.client.post("/sale-points/1/orders", json={
            "description": "Venda do dia 2026-10-01", "status": True,
            "total_value": 84, "order_date": "2026-10-01",
            "items": [{"product_id": product, "quantity": 2.0}],
        })
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["total_value"], 84)
        self.assertEqual(response.json()["item_order"][0]["name"], "Queijo")
        with self.sessions() as session:
            item = session.query(ItemsOrder).one()
            self.assertEqual(item.product_name, "Queijo")
            self.assertEqual(session.get(RetiradaProduto, outbound_id).remaining_quantity, 1)

    def test_offline_order_retry_keeps_same_id_and_deducts_once(self):
        outbound_id, product_id = self.outbound(remaining=4, sold=0)
        payload = {'client_request_id': 'offline-sale-123',
                   'items': [{'product_id': product_id, 'quantity': 2}]}
        first = self.client.post('/sale-points/1/orders', json=payload)
        second = self.client.post('/sale-points/1/orders', json=payload)
        self.assertEqual(first.status_code, 201, first.text)
        self.assertEqual(second.status_code, 201, second.text)
        self.assertEqual(first.json()['id'], second.json()['id'])
        with self.sessions() as session:
            self.assertEqual(session.query(Order).count(), 1)
            self.assertEqual(session.get(RetiradaProduto, outbound_id).remaining_quantity, 2)

    def test_product_creation_retry_and_key_conflict(self):
        payload = {'client_request_id': 'product-offline-key', 'name': 'Queijo offline', 'price': 30, 'kg': 10}
        first = self.client.post('/products', json=[payload])
        second = self.client.post('/products', json=[payload])
        self.assertEqual(first.status_code, 201, first.text)
        self.assertEqual(second.json(), first.json())
        conflict = self.client.post('/products', json=[{**payload, 'kg': 20}])
        self.assertEqual(conflict.status_code, 409)
        with self.sessions() as session:
            self.assertEqual(session.query(Product).count(), 1)
            self.assertEqual(session.query(Product).one().kg, 10)

    def test_outbound_retry_deducts_warehouse_once(self):
        product_id = self.product()
        payload = {'client_request_id': 'outbound-offline-key', 'outbound_date': '2026-09-30',
                   'produtos': [{'product_id': product_id, 'quantidade': 3, 'unidade': 'liters'}]}
        first = self.client.post('/sale-points/1/outbounds', json=payload)
        second = self.client.post('/sale-points/1/outbounds', json=payload)
        self.assertEqual(first.status_code, 201, first.text)
        self.assertEqual(second.json(), first.json())
        with self.sessions() as session:
            self.assertEqual(session.get(Product, product_id).liters, 7)
            self.assertEqual(session.query(RetiradaProduto).count(), 1)
            self.assertEqual(session.query(RetiradaProduto).one().data.date().isoformat(), '2026-09-30')

    def test_order_retry_after_delete_does_not_recreate_sale(self):
        _, product_id = self.outbound(remaining=4, sold=0)
        payload = {'client_request_id': 'order-deleted-key', 'items': [{'product_id': product_id, 'quantity': 2}]}
        first = self.client.post('/sale-points/1/orders', json=payload)
        self.assertEqual(first.status_code, 201, first.text)
        order_id = first.json()['id']
        self.assertEqual(self.client.delete(f'/orders/{order_id}').status_code, 200)
        retry = self.client.post('/sale-points/1/orders', json=payload)
        self.assertEqual(retry.json()['id'], order_id)
        with self.sessions() as session:
            self.assertEqual(session.query(Order).count(), 0)

    def test_order_key_reuse_with_different_payload_is_rejected(self):
        _, product_id = self.outbound(remaining=4, sold=0)
        payload = {'client_request_id': 'order-conflict-key', 'items': [{'product_id': product_id, 'quantity': 1}]}
        self.assertEqual(self.client.post('/sale-points/1/orders', json=payload).status_code, 201)
        response = self.client.post('/sale-points/1/orders', json={**payload, 'items': [{'product_id': product_id, 'quantity': 2}]})
        self.assertEqual(response.status_code, 409)

    def test_order_creation_legacy_units_and_item_totals_are_independent(self):
        first, milk = self.outbound(remaining=4, sold=0)
        cheese = self.product("kg", name="Queijo")
        second, _ = self.outbound("kg", cheese, remaining=3, sold=0)
        response = self.client.post("/sale-points/1/orders", json={"items": [{"product_id": milk, "liters": 1}, {"product_id": cheese, "kg": 2}]})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["total_value"], 15)
        with self.sessions() as session:
            self.assertEqual(session.get(RetiradaProduto, first).total_value, 5)
            self.assertEqual(session.get(RetiradaProduto, second).total_value, 10)

    def test_outbounds_quantity_adjustment_conserves_all_stock_units(self):
        for unit in ("amount", "kg", "liters"):
            with self.subTest(unit=unit):
                product = self.product(unit, name=unit)
                id, _ = self.outbound(unit, product)
                for target, stock in [(6, 8), (2, 12), (0, 14)]:
                    response = self.client.patch(f"/outbounds/{id}", json={"remaining_quantity": target})
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual(response.json()["remaining_quantity"], target)
                    self.assertEqual(self.client.get(f"/products/{product}").json()[unit], stock)
                self.assertEqual(self.client.get(f"/outbounds/{id}").json()["product_id"], product)

    def test_outbounds_conflicts_rollback_and_close_is_repeatable(self):
        id, product = self.outbound()
        self.assertEqual(self.client.patch(f"/outbounds/{id}", json={"remaining_quantity": 99}).status_code, 409)
        self.assertEqual(self.client.get(f"/products/{product}").json()["liters"], 10)
        for _ in range(2):
            response = self.client.patch(f"/outbounds/{id}", json={"status": False})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["remaining_quantity"], 0)
            self.assertEqual(response.json()["taken_quantity"], 5)
            self.assertEqual(self.client.get(f"/products/{product}").json()["liters"], 14)
        self.assertEqual(self.client.patch(f"/outbounds/{id}", json={"status": True}).status_code, 409)
        self.assertEqual(self.client.patch(f"/outbounds/{id}", json={"remaining_quantity": 1}).status_code, 409)
        self.assertEqual(self.client.patch(f"/outbounds/{id}", json={"observacao": ""}).json()["observacao"], "")
        self.assertEqual(self.client.patch(f"/outbounds/{id}", json={"observation": None}).status_code, 200)

    def test_outbounds_list_date_filter_invalid_payload_and_missing(self):
        id, _ = self.outbound()
        self.assertEqual(self.client.get("/outbounds").json()[0]["outbounds"][0]["id"], id)
        self.assertEqual(self.client.get("/outbounds?date=2000-01-01").json()[0]["outbounds"], [])
        for payload in [{"remaining_quantity": -1}, {"remaining_quantity": None}, {"sold_quantity": 2}, {"status": False, "remaining_quantity": 2}]:
            self.assertEqual(self.client.patch(f"/outbounds/{id}", json=payload).status_code, 422)
        self.assertEqual(self.client.patch("/outbounds/999", json={"observation": "x"}).status_code, 404)
        self.assertEqual(self.client.get("/outbounds/999").status_code, 404)
        id, _ = self.outbound("amount", self.product("amount", name="Unidade"))
        self.assertEqual(self.client.patch(f"/outbounds/{id}", json={"remaining_quantity": 1.5}).status_code, 422)

    def test_create_outbounds_returns_list_and_debits_stock(self):
        product = self.product()
        for remaining, stock in [(2, 8), (4, 6)]:
            response = self.client.post("/sale-points/1/outbounds", json={
                "produtos": [{"product_id": product, "quantidade": 2, "unidade": "liters"}],
                "observacao": "Manha",
            })
            self.assertEqual(response.status_code, 201, response.text)
            self.assertEqual(response.json()[0]["remaining_quantity"], remaining)
            self.assertEqual(self.client.get(f"/products/{product}").json()["liters"], stock)
        self.assertEqual(len(self.client.get("/outbounds").json()[0]["outbounds"]), 1)

    def test_create_outbounds_invalid_input_missing_and_atomic_conflict(self):
        product = self.product()
        item = {"product_id": product, "quantidade": 2, "unidade": "liters"}
        for changed, code in [({"quantidade": 0}, 422), ({"quantidade": -1}, 422),
                              ({"unidade": "invalid"}, 422), ({"unidade": "kg"}, 422),
                              ({"product_id": 999}, 404), ({"quantidade": 99}, 409)]:
            response = self.client.post("/sale-points/1/outbounds", json={"produtos": [{**item, **changed}]})
            self.assertEqual(response.status_code, code, response.text)
        self.assertEqual(self.client.post("/sale-points/1/outbounds", json={"produtos": []}).status_code, 422)
        self.assertEqual(self.client.post("/sale-points/999/outbounds", json={"produtos": [item]}).status_code, 404)
        self.assertEqual(self.client.get("/sale-points/999/outbounds").status_code, 404)
        self.assertEqual(self.client.get("/sale-points/999/orders").status_code, 404)
        # O primeiro item e valido, mas o segundo falha: todo o lote deve voltar.
        response = self.client.post("/sale-points/1/outbounds", json={"produtos": [item, {**item, "product_id": 999}]})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.get(f"/products/{product}").json()["liters"], 10)
        self.assertEqual(self.client.get("/outbounds").json()[0]["outbounds"], [])

    def test_validation_authentication_and_openapi(self):
        for resource in ("orders", "products", "outbounds"):
            self.assertEqual(self.client.get(f"/{resource}/0").status_code, 422)
        for resource in ("orders", "outbounds"):
            self.assertEqual(self.client.get(f"/{resource}?date=invalid").status_code, 422)
        self.assertEqual(self.client.get("/orders?status=invalid").status_code, 422)
        self.assertEqual(self.client.patch("/orders/1", json={"total_value": 10}).status_code, 422)
        schema = self.app.openapi()["paths"]
        self.assertIn("/orders", schema)
        self.assertNotIn("/pedidos/", schema)
        self.assertNotIn("/outbounds/{id}/quantity", schema)
        self.app.dependency_overrides.pop(validate_token)
        for resource in ("orders", "products", "outbounds"):
            self.assertEqual(self.client.get(f"/{resource}").status_code, 401)
            self.assertEqual(self.client.patch(f"/{resource}/1", json={}).status_code, 401)

    def test_cache_filters_preserve_old_pending_orders_and_open_outbounds(self):
        old = self.order(day=datetime(2026, 1, 1))
        pending = self.order(status=False, day=datetime(2026, 1, 1))
        recent = self.order(day=datetime(2026, 10, 1))
        url = '/sale-points/1/orders?since=2026-07-01&include_pending=true&limit=1'
        first = self.client.get(url).json()
        second = self.client.get(url + '&offset=1').json()
        self.assertEqual([row['id'] for row in first + second], [pending, recent])
        self.assertEqual(self.client.get(url + '&offset=2').json(), [])
        self.assertEqual(self.client.get('/sale-points/1/orders?date=2026-01-01').json()[0]['id'], old)
        active, product = self.outbound()
        closed, _ = self.outbound(product_id=product)
        with self.sessions() as session:
            session.get(RetiradaProduto, active).data = datetime(2026, 1, 1)
            session.get(RetiradaProduto, closed).data = datetime(2026, 1, 1)
            session.get(RetiradaProduto, closed).status = False
            session.commit()
        result = self.client.get('/sale-points/1/outbounds?since=2026-09-25&include_open=true').json()
        self.assertEqual([row['id'] for row in result['outbounds']], [active])
        self.assertEqual(len(self.client.get('/sale-points/1/outbounds?date=2026-01-01').json()['outbounds']), 2)
        self.assertEqual(self.client.get('/products?limit=1&offset=1').json(), [])
        for path in ('/products', '/sale-points/1/orders', '/sale-points/1/outbounds'):
            self.assertEqual(self.client.get(path + '?limit=501').status_code, 422)
            self.assertEqual(self.client.get(path + '?offset=-1').status_code, 422)


if __name__ == "__main__":
    unittest.main()

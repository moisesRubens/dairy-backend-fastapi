from request_helpers import request_input
"""Testes unitarios e integracao HTTP -> controller -> service -> SQLite isolado."""
import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database.model import Base, SalePoints, Token, Product, RetiradaProduto, Order, OrderSalePoint
from controllers.auth_controller import auth_router
from controllers.sale_point_controller import sale_point_router
from dependencies.sale_point_dependencies import make_session, validate_token
from schemas.sale_point_schema import SalePointCreateDTO, SalePointUpdateDTO
from controllers.sale_point_controller import edit_sale_point_controller, delete_sale_point_controller
from exceptions.sale_point_exceptions import SalePointNotFound, ExistingSalePointException
from services.sale_point_service import edit_sale_point_service, delete_all_sales_points_service, pwd_context
from services.sale_point_service import return_outbounds_service


class SalePointUnitTests(unittest.IsolatedAsyncioTestCase):
    async def test_edit_maps_missing_and_duplicate_to_http_errors(self):
        for error, code in [(SalePointNotFound(), 404), (ExistingSalePointException(), 409)]:
            with self.subTest(code=code), patch("controllers.sale_point_controller.edit_sale_point_service", new_callable=AsyncMock, side_effect=error):
                with self.assertRaises(HTTPException) as result:
                    await edit_sale_point_controller(request_input(payload={'name': 'Centro'}), user={'sub': '7'}, session=MagicMock())
                self.assertEqual(result.exception.status_code, code)

    async def test_delete_missing_returns_404(self):
        with patch("controllers.sale_point_controller.delete_sale_point_service", new_callable=AsyncMock, side_effect=SalePointNotFound()):
            with self.assertRaises(HTTPException) as result:
                await delete_sale_point_controller(request_input(), user={'sub': '7'}, session=object())
            self.assertEqual(result.exception.status_code, 404)

    async def test_patch_only_changes_supplied_fields_and_clears_email(self):
        session = MagicMock()
        point = SalePoints(id=7, name="Centro", email="old@example.com", password="stored-hash", level=1)
        session.get.return_value = point
        await edit_sale_point_service(7, SalePointUpdateDTO(email=None), session, {'sub': '7'})
        self.assertIsNone(point.email)
        self.assertEqual((point.name, point.password, point.level), ("Centro", "stored-hash", 1))
        session.begin.return_value.__exit__.assert_called_once()

    async def test_duplicate_does_not_change_or_commit_point(self):
        session = MagicMock()
        point = SalePoints(id=7, name="Centro", password="hash")
        session.get.return_value = point
        session.query.return_value.filter.return_value.first.return_value = SalePoints(id=8)
        with self.assertRaises(ExistingSalePointException):
            await edit_sale_point_service(7, SalePointUpdateDTO(name="Outro"), session, {'sub': '7'})
        self.assertEqual(point.name, "Centro")
        session.commit.assert_not_called()

    async def test_schema_normalizes_name_and_rejects_invalid_input(self):
        self.assertEqual(SalePointCreateDTO(name=" Centro ", password="secret").name, "Centro")
        for payload in [{"name": " "}, {"password": " "}, {"name": None}, {"password": None}, {"level": None}, {"level": -1}, {"id": 8}]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                SalePointUpdateDTO(**payload)

    async def test_retornar_outbound_verificar_status(self):
        for unit in ("amount", "kg", "liters"):
            with self.subTest(unit=unit):
                session = MagicMock()
                product = Product(id=2, name="Produto", price=5, **{unit: 10})
                outbound = RetiradaProduto(
                    id=3, sale_point_id=7, product_id=2, product=product,
                    taken_quantity=8, sold_quantity=3, remaining_quantity=5,
                    total_value=15, unidade=unit, status=True,
                    data=datetime(2026, 10, 1, 10), observacao="Manha",
                )
                point_query, outbound_query, product_query = MagicMock(), MagicMock(), MagicMock()
                for query in (point_query, outbound_query, product_query):
                    query.filter.return_value = query
                    query.with_for_update.return_value = query
                    query.order_by.return_value = query
                point_query.first.return_value = SalePoints(id=7)
                outbound_query.all.return_value = [outbound]
                product_query.first.return_value = product
                session.query.side_effect = [point_query, outbound_query, product_query]

                result = await return_outbounds_service(session, 7)

                self.assertFalse(outbound.status)
                self.assertEqual(outbound.remaining_quantity, 0)
                self.assertEqual(getattr(product, unit), 15)
                self.assertEqual((outbound.taken_quantity, outbound.sold_quantity, outbound.total_value), (8, 3, 15))
                self.assertFalse(result[0].status)
                session.begin.return_value.__exit__.assert_called_once()
                session.delete.assert_not_called()
                session.rollback.assert_not_called()


class SalePointIntegrationTests(unittest.TestCase):
    def test_bulk_delete_rolls_back_after_sql_deletions_and_keeps_session_open(self):
        self.create()
        self.create("Outro")
        self.promote_admin()
        with self.sessions() as session:
            product = Product(name="Leite", liters=10)
            order = Order(total_value=5)
            session.add_all([product, order])
            session.flush()
            session.add_all([
                RetiradaProduto(sale_point_id=1, product_id=product.id,
                                taken_quantity=2, remaining_quantity=2, unidade="liters"),
                OrderSalePoint(sale_point_id=1, order_id=order.id),
            ])
            session.commit()

        def assert_preserved(session):
            self.assertEqual(session.query(SalePoints).count(), 2)
            self.assertEqual(session.get(SalePoints, 1).level, 1)
            self.assertEqual(session.query(RetiradaProduto).count(), 1)
            self.assertEqual(session.query(RetiradaProduto).one().remaining_quantity, 2)
            self.assertEqual(session.query(OrderSalePoint).count(), 1)
            self.assertEqual(session.query(Product).one().liters, 10)
            self.assertEqual(session.query(Order).one().total_value, 5)

        with self.sessions() as session:
            def fail_after_deletions(current):
                current.flush()
                # Inspect SQL state before rollback, rather than ORM mocks.
                self.assertEqual(current.execute(text("SELECT COUNT(*) FROM sales_points")).scalar_one(), 0)
                self.assertEqual(current.query(RetiradaProduto).count(), 0)
                self.assertEqual(current.query(OrderSalePoint).count(), 0)
                raise RuntimeError("Failure after SQL deletions")

            event.listen(session, 'before_commit', fail_after_deletions)
            try:
                with self.assertRaisesRegex(RuntimeError, "Failure after SQL deletions"):
                    delete_all_sales_points_service(session, {'sub': '1'})
            finally:
                event.remove(session, 'before_commit', fail_after_deletions)
            self.assertFalse(session.in_transaction())
            assert_preserved(session)

        # A fresh session also sees the original committed records.
        with self.sessions() as session:
            assert_preserved(session)

    def test_retornar_e_retirar_no_mesmo_dia_cria_novo_outbound(self):
        point_id = self.create().json()["id"]
        with self.sessions() as session:
            product = Product(name="Leite", price=5, liters=20)
            session.add(product)
            session.commit()
            product_id = product.id
        url = f"/sale-points/{point_id}/outbounds"

        def withdraw(quantity):
            response = self.client.post(url, json={"produtos": [
                {"product_id": product_id, "quantidade": quantity, "unidade": "liters"}
            ]})
            self.assertEqual(response.status_code, 201, response.text)
            return response.json()[0]

        first = withdraw(8)
        self.assertTrue(first["status"])
        # Mais produtos enquanto a retirada esta ativa: mesmo registro.
        extra = withdraw(2)
        self.assertEqual(extra["id"], first["id"])
        self.assertEqual(extra["taken_quantity"], 10)
        sale = self.client.post(f"/sale-points/{point_id}/orders", json={
            "items": [{"product_id": product_id, "quantity": 3}]
        })
        self.assertEqual(sale.status_code, 201, sale.text)
        self.promote_admin()
        returned = self.client.delete(url)
        self.assertEqual(returned.status_code, 200, returned.text)
        self.assertFalse(returned.json()[0]["status"])
        self.assertEqual(returned.json()[0]["remaining_quantity"], 0)
        # Repetir devolucao nao deve devolver saldo novamente.
        self.assertEqual(self.client.delete(url).json(), [])
        with self.sessions() as session:
            self.assertEqual(session.get(Product, product_id).liters, 17)

        second = withdraw(4)
        self.assertNotEqual(second["id"], first["id"])
        self.assertTrue(second["status"])
        self.assertEqual((second["taken_quantity"], second["sold_quantity"], second["remaining_quantity"]), (4, 0, 4))
        # Venda seguinte utiliza a nova retirada, sem alterar a anterior.
        sale = self.client.post(f"/sale-points/{point_id}/orders", json={
            "items": [{"product_id": product_id, "quantity": 1}]
        })
        self.assertEqual(sale.status_code, 201, sale.text)
        history = self.client.get(url).json()["outbounds"]
        self.assertEqual(len(history), 2)
        with self.sessions() as session:
            old = session.get(RetiradaProduto, first["id"])
            new = session.get(RetiradaProduto, second["id"])
            self.assertFalse(old.status)
            self.assertEqual((old.taken_quantity, old.sold_quantity, old.remaining_quantity, old.total_value), (10, 3, 0, 15))
            self.assertTrue(new.status)
            self.assertEqual((new.taken_quantity, new.sold_quantity, new.remaining_quantity, new.total_value), (4, 1, 3, 5))
            self.assertEqual(old.data.date(), new.data.date())
            self.assertEqual(session.get(Product, product_id).liters, 13)

    def test_vender_todo_saldo_nao_encerra_outbound_automaticamente(self):
        point_id = self.create().json()["id"]
        with self.sessions() as session:
            product = Product(name="Queijo", price=5, kg=10)
            session.add(product)
            session.commit()
            product_id = product.id
        url = f"/sale-points/{point_id}/outbounds"
        payload = {"produtos": [{"product_id": product_id, "quantidade": 2, "unidade": "kg"}]}
        first = self.client.post(url, json=payload).json()[0]
        response = self.client.post(f"/sale-points/{point_id}/orders", json={
            "items": [{"product_id": product_id, "quantity": 2}]
        })
        self.assertEqual(response.status_code, 201, response.text)
        current = self.client.get(url).json()["outbounds"][0]
        self.assertTrue(current["status"])
        self.assertEqual(current["remaining_quantity"], 0)
        extra = self.client.post(url, json=payload).json()[0]
        self.assertEqual(extra["id"], first["id"])
        self.assertEqual((extra["taken_quantity"], extra["sold_quantity"], extra["remaining_quantity"]), (4, 2, 2))

    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        self.app = FastAPI()
        self.app.include_router(auth_router)
        self.app.include_router(sale_point_router)
        def session_dependency():
            with self.sessions() as session:
                yield session
        self.app.dependency_overrides[make_session] = session_dependency
        # CRUD usa identidade simulada; o teste de sessoes abaixo valida JWT real.
        self.app.dependency_overrides[validate_token] = lambda: {"sub": "1"}
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def promote_admin(self):
        with self.sessions() as session:
            session.get(SalePoints, 1).level = 1
            session.commit()

    def create(self, name="Centro"):
        response = self.client.post("/sale-points", json={"name": name, "password": "secret", "email": "a@example.com"})
        self.assertEqual(response.status_code, 201, response.text)
        return response

    def test_registration_is_seller_only(self):
        self.assertEqual(self.create().json()["level"], 0)
        self.assertEqual(self.client.post("/sale-points", json={"name": "Admin", "password": "secret", "level": 1}).status_code, 422)

    def test_admin_permissions_are_enforced_and_persisted(self):
        actor = self.create().json()["id"]
        target = self.create("Outro").json()["id"]
        url = f"/sale-points/{target}"
        self.assertEqual(self.client.patch(url, json={"level": 1}).status_code, 403)
        self.assertEqual(self.client.patch(f"/sale-points/{actor}", json={"level": 1}).status_code, 403)
        self.assertEqual(self.client.patch(url, json={"password": "takeover"}).status_code, 403)
        with self.sessions() as session:
            session.get(SalePoints, actor).level = 1
            session.commit()
        for level in [1, 0]:
            response = self.client.patch(url, json={"level": level})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(self.client.get(url).json()["level"], level)
        self.assertEqual(self.client.patch(url, json={"level": 2}).status_code, 422)
        with self.sessions() as session:
            session.get(SalePoints, actor).level = 0
            session.commit()
        self.assertEqual(self.client.patch(url, json={"level": 1}).status_code, 403)

    def test_crud_persists_returns_location_and_never_exposes_password(self):
        self.assertEqual(self.client.get("/sale-points").json(), [])
        created = self.create(" Centro ")
        point = created.json()
        self.assertEqual(created.headers["Location"], f"/sale-points/{point['id']}")
        self.assertEqual(set(point), {"id", "name", "email", "level"})
        self.assertEqual(point["name"], "Centro")
        with self.sessions() as session:
            self.assertTrue(pwd_context.verify("secret", session.get(SalePoints, point["id"]).password))
        url = created.headers["Location"]
        self.assertEqual(self.client.get(url).json(), point)
        self.assertEqual(len(self.client.get("/sale-points").json()), 1)
        updated = self.client.patch(url, json={"email": None, "name": "Novo"})
        self.assertEqual(updated.status_code, 200)
        self.assertIsNone(updated.json()["email"])
        self.assertEqual(self.client.get(url).json()["name"], "Novo")
        self.promote_admin()
        deleted = self.client.delete(url)
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertEqual(deleted.json()["id"], point["id"])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.assertEqual(self.client.get("/sale-points").json(), [])

    def test_patch_missing_and_invalid_ids(self):
        self.app.dependency_overrides[validate_token] = lambda: {"sub": "999"}
        self.assertEqual(self.client.patch("/sale-points/999", json={"name": "Novo"}).status_code, 404)
        for method in ["get", "patch", "delete"]:
            for id in ["0", "-1", "abc"]:
                kwargs = {"json": {"name": "Novo"}} if method == "patch" else {}
                self.assertEqual(getattr(self.client, method)(f"/sale-points/{id}", **kwargs).status_code, 422)

    def test_duplicates_case_insensitive_and_own_name_allowed(self):
        first = self.create()
        with self.sessions() as session:
            session.get(SalePoints, first.json()["id"]).level = 1
            session.commit()
        self.assertEqual(self.client.post("/sale-points", json={"name": "centro", "password": "secret"}).status_code, 409)
        other = self.create("Outro")
        self.assertEqual(self.client.patch(other.headers["Location"], json={"name": "CENTRO"}).status_code, 409)
        self.assertEqual(self.client.get(other.headers["Location"]).json()["name"], "Outro")
        self.assertEqual(self.client.patch(first.headers["Location"], json={"name": "CENTRO"}).status_code, 200)

    def test_partial_patch_preserves_fields_and_hashes_new_password(self):
        created = self.create()
        url = created.headers["Location"]
        self.assertEqual(self.client.patch(url, json={}).json(), created.json())
        self.assertEqual(self.client.patch(url, json={"password": "new-secret"}).status_code, 200)
        with self.sessions() as session:
            point = session.get(SalePoints, created.json()["id"])
            self.assertTrue(pwd_context.verify("new-secret", point.password))
            self.assertEqual((point.name, point.email), ("Centro", "a@example.com"))

    def test_invalid_payloads_do_not_modify_database(self):
        point = self.create()
        for data in [{"name": " "}, {"password": " "}, {"name": None}, {"level": -1}, {"unknown": 1}]:
            self.assertEqual(self.client.patch(point.headers["Location"], json=data).status_code, 422)
        self.assertEqual(self.client.get(point.headers["Location"]).json(), point.json())
        self.assertEqual(self.client.post("/sale-points", json={"name": " ", "password": "secret"}).status_code, 422)

    def test_bulk_delete_returns_snapshots_and_revokes_deleted_actor_access(self):
        self.create()
        self.create("Outro")
        self.promote_admin()
        response = self.client.delete("/sale-points")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(self.client.get("/sale-points").json(), [])
        self.assertEqual(self.client.delete("/sale-points").status_code, 403)

    def test_bulk_delete_removes_point_relationships_and_preserves_products_and_orders(self):
        point_id = self.create().json()["id"]
        with self.sessions() as session:
            product = Product(name="Leite", liters=10)
            order = Order(total_value=5)
            session.add_all([product, order])
            session.flush()
            session.add_all([
                RetiradaProduto(sale_point_id=point_id, product_id=product.id,
                                taken_quantity=2, remaining_quantity=2, unidade="liters"),
                OrderSalePoint(sale_point_id=point_id, order_id=order.id),
            ])
            session.commit()
        self.promote_admin()
        self.assertEqual(self.client.delete("/sale-points").status_code, 200)
        with self.sessions() as session:
            self.assertEqual(session.query(SalePoints).count(), 0)
            self.assertEqual(session.query(RetiradaProduto).count(), 0)
            self.assertEqual(session.query(OrderSalePoint).count(), 0)
            self.assertEqual(session.query(Product).count(), 1)
            self.assertEqual(session.query(Order).count(), 1)

    def test_protected_crud_requires_authentication(self):
        self.app.dependency_overrides.pop(validate_token)
        for method, url, kwargs in [("get", "/sale-points", {}), ("get", "/sale-points/1", {}), ("patch", "/sale-points/1", {"json": {"name": "Novo"}}), ("delete", "/sale-points/1", {}), ("delete", "/sale-points", {})]:
            self.assertEqual(getattr(self.client, method)(url, **kwargs).status_code, 401)

    def test_real_login_profile_logout_and_revoked_token(self):
        self.create()
        self.app.dependency_overrides.pop(validate_token)
        with patch.dict(os.environ, {"SECRET_KEY": "integration-secret-key-with-32-characters", "ALGORITHM": "HS256", "EXPIRE_TIME_TOKEN": "30"}):
            response = self.client.post("/auth/sessions", data={"username": "Centro", "password": "secret"})
            self.assertEqual(response.status_code, 201)
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            self.assertEqual(self.client.get("/sale-points/1", headers=headers).status_code, 200)
            self.assertEqual(self.client.post("/auth/sessions", data={"username": "Centro", "password": "wrong"}).status_code, 401)
            response = self.client.delete("/auth/sessions/current", headers=headers)
            self.assertEqual((response.status_code, response.content), (204, b""))
            with self.sessions() as session:
                self.assertIsNotNone(session.get(Token, token))
            self.assertEqual(self.client.get("/sale-points/1", headers=headers).status_code, 401)


if __name__ == "__main__":
    unittest.main()

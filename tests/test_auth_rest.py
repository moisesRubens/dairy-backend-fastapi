"""Contrato HTTP das sessoes e pontos de venda, sem acesso ao banco."""

import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from schemas.sale_point_schema import SalePointResponseDTO
from controllers.auth_controller import auth_router
from controllers.sale_point_controller import sale_point_router
from dependencies.sale_point_dependencies import make_session, validate_token


class AuthRestTests(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()
        self.session.get.return_value = SalePointResponseDTO(id=7, name="Centro", email=None, level=0)
        app = FastAPI()
        app.include_router(auth_router)
        app.include_router(sale_point_router)
        app.dependency_overrides[make_session] = lambda: self.session
        self.app = app
        self.client = TestClient(app)

    def authenticate(self):
        self.app.dependency_overrides[validate_token] = lambda: {"sub": "7"}
        return {"Authorization": "Bearer example-token"}

    def test_create_session_accepts_oauth_form(self):
        with patch("controllers.auth_controller.login_service", return_value="jwt") as controller:
            response = self.client.post("/auth/sessions", data={"username": "Centro", "password": "secret"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"access_token": "jwt", "token_type": "bearer"})
        form, session = controller.call_args.args
        self.assertEqual((form.username, form.password), ("Centro", "secret"))
        self.assertIs(session, self.session)

    def test_delete_current_session_revokes_token_and_has_no_body(self):
        with patch("controllers.auth_controller.logout_service", new_callable=AsyncMock) as controller:
            response = self.client.delete("/auth/sessions/current", headers=self.authenticate())
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        controller.assert_awaited_once_with("example-token", self.session)

    def test_protected_routes_require_token(self):
        self.assertEqual(self.client.delete("/auth/sessions/current").status_code, 401)
        self.assertEqual(self.client.patch("/sale-points/7", json={"name": "Centro"}).status_code, 401)

    def test_create_sale_point_uses_json_body(self):
        with patch("controllers.sale_point_controller.create_sale_point_service", new_callable=AsyncMock, return_value=SalePointResponseDTO(id=7, name="Centro", email=None, level=0)) as controller:
            response = self.client.post("/sale-points", json={"name": "Centro", "password": "secret", "email": "a@example.com"})
        self.assertEqual(response.status_code, 201)
        dto, session = controller.await_args.args
        self.assertEqual((dto.name, dto.email, dto.password), ('Centro', 'a@example.com', 'secret'))
        self.assertIs(session, self.session)
        self.assertEqual(self.client.post("/sale-points", params={"name": "Centro", "password": "secret"}).status_code, 422)

    def test_patch_uses_path_id_and_json_body(self):
        with patch("controllers.sale_point_controller.edit_sale_point_service", new_callable=AsyncMock, return_value=SalePointResponseDTO(id=7, name="Centro", email=None, level=0)) as controller:
            response = self.client.patch("/sale-points/7", json={"name": "Novo"}, headers=self.authenticate())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(controller.await_args.args[0], 7)
        self.assertEqual(controller.await_args.args[1].model_dump(exclude_unset=True), {"name": "Novo"})
        self.assertIs(controller.await_args.args[2], self.session)

    def test_openapi_separates_resources_and_updates_oauth_url(self):
        schema = self.app.openapi()
        self.assertEqual(set(path for path in schema["paths"] if path.startswith("/auth")), {"/auth/sessions", "/auth/sessions/current"})
        self.assertIn("/sale-points/{id}/orders", schema["paths"])
        self.assertIn("/sale-points/{id}/outbounds", schema["paths"])
        self.assertEqual(schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]["flows"]["password"]["tokenUrl"], "/auth/sessions")


if __name__ == "__main__":
    unittest.main()

from request_helpers import request_input
from fastapi import HTTPException
from starlette.requests import Request
"""Testes unitarios de GET /sale-points/{id}/outbounds, sem banco ou API externos."""

import sys
import unittest
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

# O backend usa imports absolutos a partir do diretorio app.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.model import RetiradaProduto, SalePoints
from controllers.sale_point_controller import get_outbounds_sale_point_controller as get_outbounds


class GetAuthOutboundsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.query = MagicMock()
        self.session.query.return_value = self.query
        self.query.filter.return_value = self.query
        self.query.options.return_value = self.query
        self.query.order_by.return_value = self.query
        self.query.offset.return_value = self.query
        self.query.limit.return_value = self.query
        self.query.all.return_value = []
        self.session.get.return_value = SimpleNamespace(name="Ponto Centro")

    def outbound(self, **changes):
        values = {
            "id": 1,
            "sale_point_id": 7,
            "product_id": 10,
            "product": SimpleNamespace(name="Leite", price=5.0),
            "status": True,
            "data": datetime(2026, 10, 1, 9, 30),
            "unidade": "liters",
            "taken_quantity": 10.0,
            "sold_quantity": 3.0,
            "remaining_quantity": 7.0,
            "total_value": 15.0,
            "observacao": "Retirada da manha",
        }
        values.update(changes)
        return SimpleNamespace(**values)

    async def test_retorna_nome_do_ponto_e_campos_das_retiradas(self):
        self.query.all.return_value = [self.outbound()]

        result = await get_outbounds(
            http_request=Request({'type': 'http', 'path_params': {'id': '7'}, 'query_string': b''}), user={"sub": "7"}, session=self.session
        )

        self.assertEqual(
            jsonable_encoder(result),
            {
                "sale_point_name": "Ponto Centro",
                "outbounds": [{
                    "id": 1,
                    "sale_point_id": 7,
                    "product_id": 10,
                    "name": "Leite",
                    "price": 5.0,
                    "status": True,
                    "data": "2026-10-01T09:30:00",
                    "unidade": "liters",
                    "taken_quantity": 10.0,
                    "sold_quantity": 3.0,
                    "remaining_quantity": 7.0,
                    "total_value": 15.0,
                    "observacao": "Retirada da manha",
                }],
            },
        )
        self.session.query.assert_called_once_with(RetiradaProduto)
        self.session.get.assert_called_once_with(SalePoints, 7)
        point_filter = self.query.filter.call_args_list[0].args[0]
        self.assertEqual(point_filter.compile().params, {"sale_point_id_1": 7})
        self.assertEqual(self.query.filter.call_count, 1)
        self.session.commit.assert_not_called()

    async def test_retorna_lista_vazia_quando_nao_ha_retiradas(self):
        result = await get_outbounds(
            http_request=Request({'type': 'http', 'path_params': {'id': '7'}, 'query_string': b''}), user={"sub": "7"}, session=self.session
        )

        self.assertEqual(result, {"sale_point_name": "Ponto Centro", "outbounds": []})

    async def test_aplica_filtro_de_data_quando_informado(self):
        selected_date = date(2026, 10, 1)

        await get_outbounds(
            http_request=Request({'type': 'http', 'path_params': {'id': '7'}, 'query_string': b'date=2026-10-01'}), user={"sub": "7"}, session=self.session
        )

        self.assertEqual(self.query.filter.call_count, 2)
        date_filter = self.query.filter.call_args_list[1].args[0]
        self.assertTrue(date_filter.compare(func.date(RetiradaProduto.data) == selected_date))
        self.assertEqual(list(date_filter.compile().params.values()), [selected_date])

    async def test_converte_todas_as_retiradas_inclusive_encerradas(self):
        self.query.all.return_value = [
            self.outbound(),
            self.outbound(id=2, status=False, observacao=None, remaining_quantity=0),
        ]

        result = jsonable_encoder(await get_outbounds(
            http_request=Request({'type': 'http', 'path_params': {'id': '7'}, 'query_string': b''}), user={"sub": "7"}, session=self.session
        ))

        self.assertEqual([item["id"] for item in result["outbounds"]], [1, 2])
        self.assertFalse(result["outbounds"][1]["status"])
        self.assertIsNone(result["outbounds"][1]["observacao"])

    async def test_rota_encaminha_id_data_sessao_e_retorna_resultado(self):
        expected = {"sale_point_name": "Ponto Centro", "outbounds": []}
        selected_date = date(2026, 10, 1)
        with patch(
            "controllers.sale_point_controller.get_products_by_sale_point_service",
            new_callable=AsyncMock,
            return_value=expected,
        ) as controller:
            result = await get_outbounds(
                http_request=Request({'type': 'http', 'path_params': {'id': '7'}, 'query_string': b'date=2026-10-01'}), user={"sub": "7"}, session=self.session
            )

        self.assertIs(result, expected)
        controller.assert_awaited_once_with(7, self.session, selected_date, False, since=None, include_open=False, limit=200, offset=0)

    async def test_controller_encaminha_parametros_para_servico(self):
        expected = {"sale_point_name": "Ponto Centro", "outbounds": []}
        with patch(
            "controllers.sale_point_controller.get_products_by_sale_point_service",
            new_callable=AsyncMock,
            return_value=expected,
        ) as service:
            result = await get_outbounds(request_input(), session=self.session, user={'sub': '7'})

        self.assertIs(result, expected)
        service.assert_awaited_once_with(7, self.session, None, False, since=None, include_open=False, limit=200, offset=0)

    async def test_controller_propaga_falha_do_servico(self):
        with patch(
            "controllers.sale_point_controller.get_products_by_sale_point_service",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Falha na consulta"),
        ):
            with self.assertRaisesRegex(RuntimeError, "Falha na consulta"):
                await get_outbounds(request_input(), session=self.session, user={'sub': '7'})


if __name__ == "__main__":
    unittest.main()

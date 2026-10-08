"""Controllers own validation, including requests FastAPI would reject early."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import ValidationError
from schemas.input_dto import _parse_model as parse_model, _parse_value as parse_value
from schemas.product_schema import ProductRequestDTO, ProductUpdateDTO
from schemas.order_schema import ItemOrderRequestDTO, OrderRequestDTO, OrderUpdateDTO
from schemas.outbound_schema import OutboundRequestDTO
from schemas.sale_point_schema import SalePointCreateDTO
from controllers.product_controller import product_router
from controllers.auth_controller import auth_router
from dependencies.sale_point_dependencies import validate_token
from dependencies.dependencies import make_session


class ControllerInputTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(product_router)
        app.include_router(auth_router)
        app.dependency_overrides[validate_token] = lambda: {'sub': '1'}
        app.dependency_overrides[make_session] = lambda: object()

        @app.exception_handler(RequestValidationError)
        async def reject_automatic_validation(request, error):
            raise AssertionError('FastAPI validated controller input')

        self.client = TestClient(app)
        self.app = app

    def test_invalid_http_inputs_are_handled_inside_controller(self):
        with patch('controllers.product_controller.create_product_service') as service:
            for payload in (None, {}, [], [{'name': 'x', 'price': 1, 'amount': 1.5}],
                            [{'name': 'x', 'price': -1, 'kg': 2}],
                            [{'name': 'x', 'price': 1, 'kg': 2, 'extra': True}]):
                with self.subTest(payload=payload):
                    response = self.client.post('/products', json=payload)
                    self.assertEqual(response.status_code, 422, response.text)
                    self.assertIsInstance(response.json()['detail'], str)
            service.assert_not_called()
        for path in ('/products/abc', '/products/0', '/products?limit=501',
                     '/products?offset=-1', '/products?limit=1.5'):
            self.assertEqual(self.client.get(path).status_code, 422)
        self.assertEqual(self.client.post('/products', content='{').status_code, 422)
        self.assertEqual(self.client.post('/products').status_code, 422)

    def test_form_errors_are_controller_errors(self):
        for form in ({}, {'username': 'x'}, {'username': ' ', 'password': 'x'}):
            response = self.client.post('/auth/sessions', data=form)
            self.assertEqual(response.status_code, 422)
            self.assertIsInstance(response.json()['detail'], str)

    def test_parser_raises_builtin_errors_and_preserves_partial_update(self):
        for payload in ({}, {'name': ' ', 'price': 1, 'kg': 2},
                        {'name': [], 'price': 1, 'kg': 2}):
            try:
                parse_model(ProductRequestDTO, payload)
            except (ValueError, TypeError) as error:
                self.assertNotIsInstance(error, ValidationError)
            else:
                self.fail('Invalid input accepted')
        dto = parse_model(ProductUpdateDTO, {'price': 0})
        self.assertEqual(dto.model_dump(exclude_unset=True), {'price': 0})
        self.assertEqual(parse_value('9007199254740993', int), 9007199254740993)

    def test_openapi_preserves_request_contracts(self):
        paths = self.app.openapi()['paths']
        body = paths['/products']['post']['requestBody']['content']['application/json']['schema']
        self.assertEqual(body['items']['properties']['price']['minimum'], 0)
        parameters = paths['/products']['get']['parameters']
        self.assertEqual(next(p for p in parameters if p['name'] == 'limit')['schema']['maximum'], 500)

    def test_request_dto_constructors_raise_builtin_errors(self):
        for model, payload in (
            (ProductRequestDTO, {'name': [], 'price': 1, 'kg': 2}),
            (OrderRequestDTO, {'items': [{'product_id': 1, 'quantity': -1}]}),
            (OrderUpdateDTO, {'total_value': 10}),
            (OutboundRequestDTO, {'remaining_quantity': None}),
            (SalePointCreateDTO, {'name': ' ', 'password': 'secret'}),
        ):
            with self.subTest(model=model.__name__):
                try:
                    model(**payload)
                except (ValueError, TypeError) as error:
                    self.assertNotIsInstance(error, ValidationError)
                else:
                    self.fail('Invalid DTO input accepted')
        item = ItemOrderRequestDTO(product_id=1, quantity=2)
        self.assertIs(OrderRequestDTO(items=[item]).items[0], item)


if __name__ == '__main__':
    unittest.main()

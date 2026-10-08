from request_helpers import request_input
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from exceptions.product_exceptions import ProductNotFound, BusinessConflict, InsuficientProductsAmountException
from exceptions.sale_point_exceptions import SalePointNotFound
from fastapi import HTTPException
from controllers.sale_point_controller import get_outbounds_sale_point_controller

class ControllerErrorTests(unittest.IsolatedAsyncioTestCase):
    async def invoke_error(self, error):
        with patch('controllers.sale_point_controller.get_products_by_sale_point_service', side_effect=error):
            with self.assertRaises(HTTPException) as caught:
                await get_outbounds_sale_point_controller(request_input(id=1), session=object(), user={'sub': '1'})
        return caught.exception

    async def test_status_codes(self):
        for error, code in [(SalePointNotFound(), 404), 
                             (ValueError('invalid'), 422),
                            (TypeError('invalid'), 422)]:
            with self.subTest(code=code):
                self.assertEqual((await self.invoke_error(error)).status_code, code)

    async def test_preserves_http_exception(self):
        error = HTTPException(403, 'Forbidden')
        self.assertIs(await self.invoke_error(error), error)

    async def test_unexpected_error_reaches_global_handler_unchanged(self):
        error = RuntimeError('private')
        with patch('controllers.sale_point_controller.get_products_by_sale_point_service', side_effect=error):
            with self.assertRaises(RuntimeError) as caught:
                await get_outbounds_sale_point_controller(request_input(id=1), session=object(), user={'sub': '1'})
        self.assertIs(caught.exception, error)

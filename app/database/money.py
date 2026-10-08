"""BRL amounts: decimal arithmetic, half-up cents, integer persistence."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Annotated
from functools import lru_cache
from pydantic import BeforeValidator, PlainSerializer
from sqlalchemy import BigInteger, Integer, inspect
from sqlalchemy.types import TypeDecorator

CENT = Decimal('0.01')
MAX_AMOUNT = Decimal('999999999999.99')


def money(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise TypeError('Expected a monetary amount')
    try:
        result = Decimal(str(value))
        if not result.is_finite() or abs(result) > MAX_AMOUNT:
            raise ValueError('Monetary amount must be finite and within range')
        return result.quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation as error:
        raise ValueError('Invalid monetary amount') from error


def subtotal(price, quantity):
    return money(money(price) * Decimal(str(quantity)))


# Keep existing JSON numeric contracts; floats are used only at the transport boundary.
Money = Annotated[Decimal, BeforeValidator(money),
                  PlainSerializer(lambda value: float(value), return_type=float, when_used='json')]


class MoneyColumn(TypeDecorator):
    impl = BigInteger
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else int(money(value) * 100)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, int):
            raise ValueError('Monetary schema is not in integer cents; run alembic upgrade head')
        return Decimal(value) / 100


@lru_cache(maxsize=8)
def ensure_money_schema(engine):
    """Never interpret legacy reais as cents or write cents into legacy columns."""
    schema = inspect(engine)
    for table, names in {'products': ['price'], 'orders': ['total_value', 'discount_value'],
                         'item_order': ['item_price'], 'retiradas_produto': ['total_value']}.items():
        columns = {column['name']: column['type'] for column in schema.get_columns(table)}
        if any(not isinstance(columns.get(name), Integer) for name in names):
            raise RuntimeError('Monetary schema requires migration: run alembic upgrade head')

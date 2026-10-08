import math
import types
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from typing import Annotated, Literal, Union, get_origin, get_args
from pydantic import BaseModel

def _parse_value(value, annotation):
    origin, args = (get_origin(annotation), get_args(annotation))
    if origin is Annotated:
        result = _parse_value(value, args[0])
        _check_constraints(result, args[1:])
        return result
    if origin in (Union, types.UnionType):
        if value is None and type(None) in args:
            return None
        for option in args:
            if option is type(None):
                continue
            try:
                return _parse_value(value, option)
            except (ValueError, TypeError):
                pass
        raise ValueError('Invalid value')
    if origin is Literal:
        if value not in args:
            raise ValueError(f'Expected one of {args}')
        return value
    if origin is list:
        if not isinstance(value, list):
            raise TypeError('Expected a list')
        return [_parse_value(item, args[0]) for item in value]
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        if isinstance(value, annotation):
            return value
        return _parse_model(annotation, value)
    if annotation is str:
        if not isinstance(value, str):
            raise TypeError('Expected a string')
        return value
    if annotation is bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.lower() in ('true', 'false', '1', '0'):
            return value.lower() in ('true', '1')
        raise TypeError('Expected a boolean')
    if annotation in (int, float):
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise TypeError('Expected a number')
        if annotation is int:
            try:
                number = Decimal(str(value))
            except InvalidOperation as error:
                raise ValueError('Expected an integer') from error
            if not number.is_finite() or number != number.to_integral_value():
                raise ValueError('Expected a finite integer')
            return int(number)
        try:
            number = float(value)
        except OverflowError as error:
            raise ValueError('Number must be finite') from error
        if not math.isfinite(number):
            raise ValueError('Number must be finite')
        return number
    if annotation is Decimal:
        from database.money import money
        return money(value)
    if annotation in (date, datetime):
        if type(value) is annotation:
            return value
        if not isinstance(value, str):
            raise TypeError('Expected an ISO date')
        return annotation.fromisoformat(value.replace('Z', '+00:00'))
    return value

def _check_constraints(value, metadata):
    if value is None:
        return
    for constraint in metadata:
        _check_constraints(value, getattr(constraint, 'metadata', ()))
        for name, invalid in (('gt', lambda bound: value <= bound), ('ge', lambda bound: value < bound), ('lt', lambda bound: value >= bound), ('le', lambda bound: value > bound), ('min_length', lambda bound: len(value) < bound), ('max_length', lambda bound: len(value) > bound)):
            bound = getattr(constraint, name, None)
            if bound is not None and invalid(bound):
                raise ValueError(f'Value violates {name}={bound}')

def _parse_model(model, payload):
    if not isinstance(payload, dict):
        raise TypeError('Expected a JSON object')
    fields = model.model_fields
    allowed = set(fields) | {field.alias for field in fields.values() if field.alias}
    if model.model_config.get('extra') == 'forbid' and set(payload) - allowed:
        raise ValueError('Unknown fields: ' + ', '.join(sorted(set(payload) - allowed)))
    values, supplied = ({}, set())
    for name, field in fields.items():
        key = field.alias if field.alias in payload else name
        if key not in payload:
            if field.is_required():
                raise ValueError(f'Missing field: {name}')
            values[name] = field.get_default(call_default_factory=True)
            continue
        supplied.add(name)
        value = _parse_value(payload[key], field.annotation)
        _check_constraints(value, field.metadata)
        for validator in model.__pydantic_decorators__.field_validators.values():
            if name in validator.info.fields:
                value = validator.func(value)
        values[name] = value
    result = model.model_construct(_fields_set=supplied, **values)
    for validator in model.__pydantic_decorators__.model_validators.values():
        result = validator.func(result)
    return result

class InputDTO(BaseModel):
    """Request DTOs validate explicitly and raise ValueError or TypeError."""
    def __init__(self, **payload):
        parsed = _parse_model(type(self), payload)
        for name in ('__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'):
            object.__setattr__(self, name, getattr(parsed, name))

    @classmethod
    def from_payload(cls, payload):
        return _parse_model(cls, payload)

    @classmethod
    def from_list(cls, payload):
        if not isinstance(payload, list):
            raise TypeError('Expected a list')
        if not payload:
            raise ValueError('Supply at least one item')
        return [cls.from_payload(item) for item in payload]

class RequestParameters(InputDTO):
    @staticmethod
    def parse(value, annotation):
        return _parse_value(value, annotation)

    @staticmethod
    def positive_id(value):
        result = _parse_value(value, int)
        if result <= 0:
            raise ValueError('ID must be positive')
        return result

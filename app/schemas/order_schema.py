from database.money import Money
from schemas.input_dto import InputDTO
from typing import List, Optional, Literal
from datetime import datetime, date
from pydantic import Field, ConfigDict, model_validator, field_validator, BaseModel
from fastapi import Path
from schemas.product_schema import ProductResponseDTO

class ItemOrderRequestDTO(InputDTO):
    model_config = ConfigDict(extra='forbid')
    product_id: int = Field(gt=0)
    quantity: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    amount: int | None = Field(default=None, gt=0)
    kg: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    liters: float | None = Field(default=None, gt=0, allow_inf_nan=False)

    @model_validator(mode='after')
    def one_quantity(self):
        if sum((value is not None for value in (self.quantity, self.amount, self.kg, self.liters))) != 1:
            raise ValueError('Supply exactly one quantity')
        return self

class ItemOrderResponseDTO(BaseModel):
    product_id: int | None
    name: str
    price: Money = Field(validation_alias='item_price')
    amount: Optional[int] = None
    kg: Optional[float] = None
    liters: Optional[float] = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class OrderResponse(BaseModel):
    id: int
    status: bool
    order_status: Literal['pago', 'pendente', 'desconto'] | None = None
    total_value: Money
    description: str | None = None
    date: datetime = Field(alias='order_date')
    items: List[ItemOrderResponseDTO] = Field(alias='item_order')
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class OrderRequestDTO(InputDTO):
    client_request_id: str | None = Field(default=None, min_length=1, max_length=80)
    description: Optional[str] = None
    status: Optional[bool] = None
    order_status: Literal['pago', 'pendente', 'desconto'] | None = None
    total_value: Money | None = Field(default=None, gt=0, allow_inf_nan=False)
    order_date: Optional[date] = None
    items: List[ItemOrderRequestDTO] = Field(min_length=1)

class ItemOrderResponseDTO2(BaseModel):
    prodcut: ProductResponseDTO
    price: Money
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class OrderResponseDTO(BaseModel):
    id: int
    status: bool
    order_status: Literal['pago', 'pendente', 'desconto'] | None = None
    total_value: Money
    description: str | None = None
    date: datetime = Field(validation_alias='order_date')
    sale_point_id: int | None
    item_order: List[ItemOrderResponseDTO]
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class OrderUpdateDTO(InputDTO):
    model_config = ConfigDict(extra='forbid')
    description: str | None = Field(default=None, max_length=200)
    status: bool | None = None
    order_status: Literal['pago', 'pendente', 'desconto'] | None = None
    total_value: Money | None = Field(default=None, gt=0, allow_inf_nan=False)
    order_date: date | None = None

    @model_validator(mode='after')
    def validate_final_value(self):
        if self.total_value is not None and self.order_status is None:
            raise ValueError('Supply order_status with total_value')
        return self

    @field_validator('status', 'order_date')
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError('Field must not be null')
        return value

# HTTP input documentation; validation is performed by request DTOs.
ENDPOINT_DOCS = {'index': {'parameters': [{'name': 'date',
                           'in': 'query',
                           'required': False,
                           'schema': {'anyOf': [{'format': 'date', 'type': 'string'},
                                                {'type': 'null'}],
                                      'default': None}},
                          {'name': 'description',
                           'in': 'query',
                           'required': False,
                           'schema': {'anyOf': [{'type': 'string'}, {'type': 'null'}],
                                      'default': None}},
                          {'name': 'status',
                           'in': 'query',
                           'required': False,
                           'schema': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}],
                                      'default': None}}]},
 'show': {'parameters': [{'name': 'id',
                          'in': 'path',
                          'required': True,
                          'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]},
 'edit': {'requestBody': {'required': True,
                          'content': {'application/json': {'schema': {'additionalProperties': False,
                                                                      'properties': {'description': {'anyOf': [{'maxLength': 200,
                                                                                                                'type': 'string'},
                                                                                                               {'type': 'null'}],
                                                                                                     'default': None,
                                                                                                     'title': 'Description'},
                                                                                     'status': {'anyOf': [{'type': 'boolean'},
                                                                                                          {'type': 'null'}],
                                                                                                'default': None,
                                                                                                'title': 'Status'},
                                                                                     'order_status': {'anyOf': [{'enum': ['pago',
                                                                                                                          'pendente',
                                                                                                                          'desconto'],
                                                                                                                 'type': 'string'},
                                                                                                                {'type': 'null'}],
                                                                                                      'default': None,
                                                                                                      'title': 'Order '
                                                                                                               'Status'},
                                                                                     'total_value': {'anyOf': [{'exclusiveMinimum': 0,
                                                                                                                'type': 'number'},
                                                                                                               {'type': 'null'}],
                                                                                                     'default': None,
                                                                                                     'title': 'Total '
                                                                                                              'Value'},
                                                                                     'order_date': {'anyOf': [{'format': 'date',
                                                                                                               'type': 'string'},
                                                                                                              {'type': 'null'}],
                                                                                                    'default': None,
                                                                                                    'title': 'Order '
                                                                                                             'Date'}},
                                                                      'title': 'OrderUpdateDTO',
                                                                      'type': 'object'}}}},
          'parameters': [{'name': 'id',
                          'in': 'path',
                          'required': True,
                          'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]},
 'destroy': {'parameters': [{'name': 'id',
                             'in': 'path',
                             'required': True,
                             'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]},
 'delete_all': {}}

from datetime import date as Date, date as DateType, datetime as DateTimeType
from typing import Annotated, Optional, Literal
from fastapi import Query

class ListOrderQueryDTO(InputDTO):
    date: Date | None = None
    description: str | None = None
    status: bool | None = None

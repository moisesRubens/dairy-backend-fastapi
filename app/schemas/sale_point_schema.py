from schemas.input_dto import InputDTO
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pydantic import Field, ConfigDict, field_validator
from schemas.order_schema import OrderResponseDTO

class SalePointResponseDTO(BaseModel):
    id: int | None
    name: str | None
    email: str | None
    level: int | None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class SalePointRequestDTO(InputDTO):
    id: int | None = None
    name: str | None = None
    email: str | None = None
    password: str | None = None
    level: int | None = None

class OrderSalePointResponseDTO(BaseModel):
    sale_point_id: int
    orders: List[OrderResponseDTO]
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class SalePointCreateDTO(InputDTO):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1)
    email: str | None = Field(default=None, max_length=200)

    @field_validator('name')
    @classmethod
    def normalize_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Name must not be blank')
        return value

    @field_validator('password')
    @classmethod
    def validate_password(cls, value):
        if not value.strip():
            raise ValueError('Password must not be blank')
        return value

class SalePointUpdateDTO(InputDTO):
    model_config = ConfigDict(extra='forbid')
    name: str | None = Field(default=None, min_length=1, max_length=100)
    password: str | None = Field(default=None, min_length=1)
    email: str | None = Field(default=None, max_length=200)
    level: int | None = Field(default=None, ge=0, le=1)

    @field_validator('name', 'password', 'level')
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError('Field must not be null')
        return value

    @field_validator('name')
    @classmethod
    def normalize_name(cls, value):
        return SalePointCreateDTO.normalize_name(value)

    @field_validator('password')
    @classmethod
    def validate_password(cls, value):
        return SalePointCreateDTO.validate_password(value)

# HTTP input documentation; validation is performed by request DTOs.
ENDPOINT_DOCS = {'index': {},
 'store': {'requestBody': {'required': True,
                           'content': {'application/json': {'schema': {'additionalProperties': False,
                                                                       'properties': {'name': {'maxLength': 100,
                                                                                               'minLength': 1,
                                                                                               'title': 'Name',
                                                                                               'type': 'string'},
                                                                                      'password': {'minLength': 1,
                                                                                                   'title': 'Password',
                                                                                                   'type': 'string'},
                                                                                      'email': {'anyOf': [{'maxLength': 200,
                                                                                                           'type': 'string'},
                                                                                                          {'type': 'null'}],
                                                                                                'default': None,
                                                                                                'title': 'Email'}},
                                                                       'required': ['name',
                                                                                    'password'],
                                                                       'title': 'SalePointCreateDTO',
                                                                       'type': 'object'}}}}},
 'edit': {'requestBody': {'required': True,
                          'content': {'application/json': {'schema': {'additionalProperties': False,
                                                                      'properties': {'name': {'anyOf': [{'maxLength': 100,
                                                                                                         'minLength': 1,
                                                                                                         'type': 'string'},
                                                                                                        {'type': 'null'}],
                                                                                              'default': None,
                                                                                              'title': 'Name'},
                                                                                     'password': {'anyOf': [{'minLength': 1,
                                                                                                             'type': 'string'},
                                                                                                            {'type': 'null'}],
                                                                                                  'default': None,
                                                                                                  'title': 'Password'},
                                                                                     'email': {'anyOf': [{'maxLength': 200,
                                                                                                          'type': 'string'},
                                                                                                         {'type': 'null'}],
                                                                                               'default': None,
                                                                                               'title': 'Email'},
                                                                                     'level': {'anyOf': [{'maximum': 1,
                                                                                                          'minimum': 0,
                                                                                                          'type': 'integer'},
                                                                                                         {'type': 'null'}],
                                                                                               'default': None,
                                                                                               'title': 'Level'}},
                                                                      'title': 'SalePointUpdateDTO',
                                                                      'type': 'object'}}}},
          'parameters': [{'name': 'id',
                          'in': 'path',
                          'required': True,
                          'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]},
 'delete_all': {},
 'sales_charts': {'parameters': [{'name': 'day',
                                  'in': 'query',
                                  'required': True,
                                  'schema': {'format': 'date', 'type': 'string'}},
                                 {'name': 'period',
                                  'in': 'query',
                                  'required': False,
                                  'schema': {'enum': ['day', 'week'],
                                             'type': 'string',
                                             'default': 'day'}}]},
 'export_sales_report': {'parameters': [{'name': 'day',
                                         'in': 'query',
                                         'required': True,
                                         'schema': {'format': 'date', 'type': 'string'}},
                                        {'name': 'period',
                                         'in': 'query',
                                         'required': False,
                                         'schema': {'enum': ['day', 'week'],
                                                    'type': 'string',
                                                    'default': 'day'}}]},
 'show': {'parameters': [{'name': 'id',
                          'in': 'path',
                          'required': True,
                          'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]},
 'destroy': {'parameters': [{'name': 'id',
                             'in': 'path',
                             'required': True,
                             'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]},
 'get_orders_by_sale_point_id': {'parameters': [{'name': 'id',
                                                 'in': 'path',
                                                 'required': True,
                                                 'schema': {'type': 'integer',
                                                            'exclusiveMinimum': 0}},
                                                {'name': 'date',
                                                 'in': 'query',
                                                 'required': False,
                                                 'schema': {'anyOf': [{'format': 'date',
                                                                       'type': 'string'},
                                                                      {'type': 'null'}],
                                                            'default': None}},
                                                {'name': 'since',
                                                 'in': 'query',
                                                 'required': False,
                                                 'schema': {'anyOf': [{'format': 'date',
                                                                       'type': 'string'},
                                                                      {'type': 'null'}],
                                                            'default': None}},
                                                {'name': 'include_pending',
                                                 'in': 'query',
                                                 'required': False,
                                                 'schema': {'type': 'boolean', 'default': False}},
                                                {'name': 'limit',
                                                 'in': 'query',
                                                 'required': False,
                                                 'schema': {'maximum': 500,
                                                            'minimum': 1,
                                                            'type': 'integer',
                                                            'default': 200}},
                                                {'name': 'offset',
                                                 'in': 'query',
                                                 'required': False,
                                                 'schema': {'minimum': 0,
                                                            'type': 'integer',
                                                            'default': 0}}]},
 'store_order': {'requestBody': {'required': True,
                                 'content': {'application/json': {'schema': {'properties': {'client_request_id': {'anyOf': [{'maxLength': 80,
                                                                                                                             'minLength': 1,
                                                                                                                             'type': 'string'},
                                                                                                                            {'type': 'null'}],
                                                                                                                  'default': None,
                                                                                                                  'title': 'Client '
                                                                                                                           'Request '
                                                                                                                           'Id'},
                                                                                            'description': {'anyOf': [{'type': 'string'},
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
                                                                                                                    'Date'},
                                                                                            'items': {'items': {'additionalProperties': False,
                                                                                                                'properties': {'product_id': {'exclusiveMinimum': 0,
                                                                                                                                              'title': 'Product '
                                                                                                                                                       'Id',
                                                                                                                                              'type': 'integer'},
                                                                                                                               'quantity': {'anyOf': [{'exclusiveMinimum': 0,
                                                                                                                                                       'type': 'number'},
                                                                                                                                                      {'type': 'null'}],
                                                                                                                                            'default': None,
                                                                                                                                            'title': 'Quantity'},
                                                                                                                               'amount': {'anyOf': [{'exclusiveMinimum': 0,
                                                                                                                                                     'type': 'integer'},
                                                                                                                                                    {'type': 'null'}],
                                                                                                                                          'default': None,
                                                                                                                                          'title': 'Amount'},
                                                                                                                               'kg': {'anyOf': [{'exclusiveMinimum': 0,
                                                                                                                                                 'type': 'number'},
                                                                                                                                                {'type': 'null'}],
                                                                                                                                      'default': None,
                                                                                                                                      'title': 'Kg'},
                                                                                                                               'liters': {'anyOf': [{'exclusiveMinimum': 0,
                                                                                                                                                     'type': 'number'},
                                                                                                                                                    {'type': 'null'}],
                                                                                                                                          'default': None,
                                                                                                                                          'title': 'Liters'}},
                                                                                                                'required': ['product_id'],
                                                                                                                'title': 'ItemOrderRequestDTO',
                                                                                                                'type': 'object'},
                                                                                                      'minItems': 1,
                                                                                                      'title': 'Items',
                                                                                                      'type': 'array'}},
                                                                             'required': ['items'],
                                                                             'title': 'OrderRequestDTO',
                                                                             'type': 'object'}}}},
                 'parameters': [{'name': 'id',
                                 'in': 'path',
                                 'required': True,
                                 'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]},
 'delete_orders': {'parameters': [{'name': 'id',
                                   'in': 'path',
                                   'required': True,
                                   'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]},
 'get_outbounds': {'parameters': [{'name': 'id',
                                   'in': 'path',
                                   'required': True,
                                   'schema': {'type': 'integer', 'exclusiveMinimum': 0}},
                                  {'name': 'date',
                                   'in': 'query',
                                   'required': False,
                                   'schema': {'anyOf': [{'format': 'date', 'type': 'string'},
                                                        {'type': 'null'}],
                                              'default': None}},
                                  {'name': 'since',
                                   'in': 'query',
                                   'required': False,
                                   'schema': {'anyOf': [{'format': 'date', 'type': 'string'},
                                                        {'type': 'null'}],
                                              'default': None}},
                                  {'name': 'include_open',
                                   'in': 'query',
                                   'required': False,
                                   'schema': {'type': 'boolean', 'default': False}},
                                  {'name': 'limit',
                                   'in': 'query',
                                   'required': False,
                                   'schema': {'maximum': 500,
                                              'minimum': 1,
                                              'type': 'integer',
                                              'default': 200}},
                                  {'name': 'offset',
                                   'in': 'query',
                                   'required': False,
                                   'schema': {'minimum': 0, 'type': 'integer', 'default': 0}}]},
 'create_outbound': {'requestBody': {'required': True,
                                     'content': {'application/json': {'schema': {'properties': {'client_request_id': {'anyOf': [{'maxLength': 80,
                                                                                                                                 'minLength': 1,
                                                                                                                                 'type': 'string'},
                                                                                                                                {'type': 'null'}],
                                                                                                                      'default': None,
                                                                                                                      'title': 'Client '
                                                                                                                               'Request '
                                                                                                                               'Id'},
                                                                                                'outbound_date': {'anyOf': [{'format': 'date',
                                                                                                                             'type': 'string'},
                                                                                                                            {'type': 'null'}],
                                                                                                                  'default': None,
                                                                                                                  'title': 'Outbound '
                                                                                                                           'Date'},
                                                                                                'produtos': {'items': {'additionalProperties': False,
                                                                                                                       'properties': {'product_id': {'exclusiveMinimum': 0,
                                                                                                                                                     'title': 'Product '
                                                                                                                                                              'Id',
                                                                                                                                                     'type': 'integer'},
                                                                                                                                      'quantidade': {'exclusiveMinimum': 0,
                                                                                                                                                     'title': 'Quantidade',
                                                                                                                                                     'type': 'number'},
                                                                                                                                      'unidade': {'enum': ['amount',
                                                                                                                                                           'kg',
                                                                                                                                                           'liters'],
                                                                                                                                                  'title': 'Unidade',
                                                                                                                                                  'type': 'string'}},
                                                                                                                       'required': ['product_id',
                                                                                                                                    'quantidade',
                                                                                                                                    'unidade'],
                                                                                                                       'title': 'ItemRetiradaDTO',
                                                                                                                       'type': 'object'},
                                                                                                             'minItems': 1,
                                                                                                             'title': 'Produtos',
                                                                                                             'type': 'array'},
                                                                                                'observacao': {'anyOf': [{'type': 'string'},
                                                                                                                         {'type': 'null'}],
                                                                                                               'default': None,
                                                                                                               'title': 'Observacao'}},
                                                                                 'required': ['produtos'],
                                                                                 'title': 'RetirarProdutosRequestDTO',
                                                                                 'type': 'object'}}}},
                     'parameters': [{'name': 'id',
                                     'in': 'path',
                                     'required': True,
                                     'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]},
 'delete_outbounds': {'parameters': [{'name': 'id',
                                      'in': 'path',
                                      'required': True,
                                      'schema': {'type': 'integer', 'exclusiveMinimum': 0}},
                                     {'name': 'before',
                                      'in': 'query',
                                      'required': False,
                                      'schema': {'anyOf': [{'format': 'date-time',
                                                            'type': 'string'},
                                                           {'type': 'null'}],
                                                 'default': None}}]},
 'return_outbounds': {'parameters': [{'name': 'id',
                                      'in': 'path',
                                      'required': True,
                                      'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]}}

from datetime import date as Date, date as DateType, datetime as DateTimeType
from typing import Annotated, Optional, Literal
from fastapi import Query

class SalesChartsSalePointQueryDTO(InputDTO):
    day: DateType
    period: Literal['day', 'week'] = 'day'

class ExportSalesReportSalePointQueryDTO(InputDTO):
    day: DateType
    period: Literal['day', 'week'] = 'day'

class GetOrdersBySalePointIdSalePointQueryDTO(InputDTO):
    date: Optional[DateType] = None
    since: Optional[DateType] = None
    include_pending: bool = False
    limit: Annotated[int, Query(ge=1, le=500)] = 200
    offset: Annotated[int, Query(ge=0)] = 0

class GetOutboundsSalePointQueryDTO(InputDTO):
    date: Optional[DateType] = None
    since: Optional[DateType] = None
    include_open: bool = False
    limit: Annotated[int, Query(ge=1, le=500)] = 200
    offset: Annotated[int, Query(ge=0)] = 0

class DeleteOutboundsSalePointQueryDTO(InputDTO):
    before: Optional[DateTimeType] = None

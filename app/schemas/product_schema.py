from database.money import Money
from schemas.input_dto import InputDTO
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime, date
from pydantic import Field, ConfigDict, field_validator, model_validator

class ProductResponseDTO(BaseModel):
    id: int
    name: str
    price: Money
    amount: float | None = -1
    kg: float | None = -1
    liters: float | None = -1
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class ProductRequestDTO(InputDTO):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    client_request_id: str | None = Field(default=None, min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=100)
    price: Money = Field(ge=0)
    amount: int | None = Field(default=None, ge=-1)
    kg: float | None = Field(default=None, ge=-1)
    liters: float | None = Field(default=None, ge=-1)

    @field_validator('name')
    @classmethod
    def normalize_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Name must not be blank')
        return value

    @field_validator('amount', 'kg', 'liters')
    @classmethod
    def normalize_unit(cls, value):
        if value == -1:
            return None
        if value is not None and value < 0:
            raise ValueError('Quantity must not be negative')
        return value

    @model_validator(mode='after')
    def one_unit(self):
        if sum((value is not None for value in (self.amount, self.kg, self.liters))) != 1:
            raise ValueError('Supply exactly one stock unit')
        return self

class ProductUpdateDTO(InputDTO):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    price: Money | None = Field(default=None, ge=0)
    amount: int | None = Field(default=None, ge=-1)
    kg: float | None = Field(default=None, ge=-1)
    liters: float | None = Field(default=None, ge=-1)

    @field_validator('name', 'price')
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError('Field must not be null')
        return value

    @field_validator('name')
    @classmethod
    def normalize_name(cls, value):
        return ProductRequestDTO.normalize_name(value)

    @field_validator('amount', 'kg', 'liters')
    @classmethod
    def normalize_unit(cls, value):
        return ProductRequestDTO.normalize_unit(value)

class ItemRetiradaDTO(InputDTO):
    model_config = ConfigDict(extra='forbid')
    product_id: int = Field(gt=0)
    quantidade: float = Field(gt=0, allow_inf_nan=False)
    unidade: Literal['amount', 'kg', 'liters']

class ItemToReturnToStorageDTO(InputDTO):
    product_id: int

class ReturnToStorageRequestDTO(InputDTO):
    products: List[ItemToReturnToStorageDTO]

class RetirarProdutosRequestDTO(InputDTO):
    client_request_id: str | None = Field(default=None, min_length=1, max_length=80)
    outbound_date: date | None = None
    produtos: List[ItemRetiradaDTO] = Field(min_length=1)
    observacao: Optional[str] = None

class ItemsRetiradaResponseDTO(BaseModel):
    id: int
    sale_point_id: int
    product_id: int
    name: str | None = None
    price: Money
    status: bool
    date: datetime = Field(alias='data')
    unit_type: str = Field(alias='unidade')
    taken_quantity: float
    sold_quantity: float
    remaining_quantity: float
    total_value_item: Money = Field(alias='total_value')
    observation: Optional[str] = Field(alias='observacao')
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @classmethod
    def from_orm(cls, retirada):
        """MÃ©todo para criar DTO a partir do modelo ORM"""
        return cls(id=retirada.id, sale_point_id=retirada.sale_point_id, product_id=retirada.product_id, name=retirada.product.name if retirada.product else None, price=retirada.product.price, status=retirada.status, date=retirada.data, unit_type=retirada.unidade, taken_quantity=retirada.taken_quantity, sold_quantity=retirada.sold_quantity, remaining_quantity=retirada.remaining_quantity, total_value_item=retirada.total_value, observation=retirada.observacao)

class RetiradaResponseDTO(BaseModel):
    retirada_id: int
    observation: str | None = None
    List[ItemsRetiradaResponseDTO]

# HTTP input documentation; validation is performed by request DTOs.
ENDPOINT_DOCS = {'index': {'parameters': [{'name': 'limit',
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
 'store': {'requestBody': {'required': True,
                           'content': {'application/json': {'schema': {'items': {'additionalProperties': False,
                                                                                 'properties': {'client_request_id': {'anyOf': [{'maxLength': 80,
                                                                                                                                 'minLength': 1,
                                                                                                                                 'type': 'string'},
                                                                                                                                {'type': 'null'}],
                                                                                                                      'default': None,
                                                                                                                      'title': 'Client '
                                                                                                                               'Request '
                                                                                                                               'Id'},
                                                                                                'name': {'maxLength': 100,
                                                                                                         'minLength': 1,
                                                                                                         'title': 'Name',
                                                                                                         'type': 'string'},
                                                                                                'price': {'minimum': 0,
                                                                                                          'title': 'Price',
                                                                                                          'type': 'number'},
                                                                                                'amount': {'anyOf': [{'minimum': -1,
                                                                                                                      'type': 'integer'},
                                                                                                                     {'type': 'null'}],
                                                                                                           'default': None,
                                                                                                           'title': 'Amount'},
                                                                                                'kg': {'anyOf': [{'minimum': -1,
                                                                                                                  'type': 'number'},
                                                                                                                 {'type': 'null'}],
                                                                                                       'default': None,
                                                                                                       'title': 'Kg'},
                                                                                                'liters': {'anyOf': [{'minimum': -1,
                                                                                                                      'type': 'number'},
                                                                                                                     {'type': 'null'}],
                                                                                                           'default': None,
                                                                                                           'title': 'Liters'}},
                                                                                 'required': ['name',
                                                                                              'price'],
                                                                                 'title': 'ProductRequestDTO',
                                                                                 'type': 'object'},
                                                                       'type': 'array'}}}}},
 'destroy': {'parameters': [{'name': 'id',
                             'in': 'path',
                             'required': True,
                             'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]},
 'show': {'parameters': [{'name': 'id',
                          'in': 'path',
                          'required': True,
                          'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]},
 'edit': {'requestBody': {'required': True,
                          'content': {'application/json': {'schema': {'additionalProperties': False,
                                                                      'properties': {'name': {'anyOf': [{'maxLength': 100,
                                                                                                         'minLength': 1,
                                                                                                         'type': 'string'},
                                                                                                        {'type': 'null'}],
                                                                                              'default': None,
                                                                                              'title': 'Name'},
                                                                                     'price': {'anyOf': [{'minimum': 0,
                                                                                                          'type': 'number'},
                                                                                                         {'type': 'null'}],
                                                                                               'default': None,
                                                                                               'title': 'Price'},
                                                                                     'amount': {'anyOf': [{'minimum': -1,
                                                                                                           'type': 'integer'},
                                                                                                          {'type': 'null'}],
                                                                                                'default': None,
                                                                                                'title': 'Amount'},
                                                                                     'kg': {'anyOf': [{'minimum': -1,
                                                                                                       'type': 'number'},
                                                                                                      {'type': 'null'}],
                                                                                            'default': None,
                                                                                            'title': 'Kg'},
                                                                                     'liters': {'anyOf': [{'minimum': -1,
                                                                                                           'type': 'number'},
                                                                                                          {'type': 'null'}],
                                                                                                'default': None,
                                                                                                'title': 'Liters'}},
                                                                      'title': 'ProductUpdateDTO',
                                                                      'type': 'object'}}}},
          'parameters': [{'name': 'id',
                          'in': 'path',
                          'required': True,
                          'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]},
 'delete_all': {}}

from datetime import date as Date, date as DateType, datetime as DateTimeType
from typing import Annotated, Optional, Literal
from fastapi import Query

class ListProductQueryDTO(InputDTO):
    limit: Annotated[int, Query(ge=1, le=500)] = 200
    offset: Annotated[int, Query(ge=0)] = 0

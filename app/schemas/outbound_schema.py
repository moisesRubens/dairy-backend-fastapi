from database.money import Money
from schemas.input_dto import InputDTO
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from schemas.product_schema import ProductResponseDTO, ItemsRetiradaResponseDTO

class OutboundRequestDTO(InputDTO):
    model_config = ConfigDict(extra='forbid', populate_by_name=True, allow_inf_nan=False)
    remaining_quantity: float | None = Field(default=None, ge=0)
    observation: str | None = Field(default=None, alias='observacao', max_length=200)
    status: bool | None = None

    @field_validator('remaining_quantity', 'status')
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError('Field must not be null')
        return value

class SalePointOutboundsDTO(BaseModel):
    sale_point_name: str
    outbounds: list[ItemsRetiradaResponseDTO]

class SalePointDailyOutboundsDTO(SalePointOutboundsDTO):
    sale_point_id: int
    sales_total: Money

class OutboundResponseDTO(BaseModel):
    id: int
    name: str | None = None
    status: bool | None = None
    date: Optional[datetime] = Field(default=None, alias='data')
    unit_type: Optional[str] = Field(default=None, alias='unidade')
    taken_quantity: float | None = None
    sold_quantity: float | None = None
    remaining_quantity: float | None = None
    total_value_item: Optional[Money] = Field(default=None, alias='total_value')
    observation: Optional[str] = Field(default=None, alias='observacao')
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class OutboundResponseDTOTest(BaseModel):
    id: int
    observation: Optional[str] = Field(default=None, alias='observacao')
    date: Optional[datetime] = Field(default=None, alias='data')
    products: list[ProductResponseDTO]

# HTTP input documentation; validation is performed by request DTOs.
ENDPOINT_DOCS = {'index': {'parameters': [{'name': 'date',
                           'in': 'query',
                           'required': False,
                           'schema': {'anyOf': [{'format': 'date', 'type': 'string'},
                                                {'type': 'null'}],
                                      'default': None}}]},
 'show': {'parameters': [{'name': 'id',
                          'in': 'path',
                          'required': True,
                          'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]},
 'edit_outbound': {'requestBody': {'required': True,
                                   'content': {'application/json': {'schema': {'additionalProperties': False,
                                                                               'properties': {'remaining_quantity': {'anyOf': [{'minimum': 0,
                                                                                                                                'type': 'number'},
                                                                                                                               {'type': 'null'}],
                                                                                                                     'default': None,
                                                                                                                     'title': 'Remaining '
                                                                                                                              'Quantity'},
                                                                                              'observacao': {'anyOf': [{'maxLength': 200,
                                                                                                                        'type': 'string'},
                                                                                                                       {'type': 'null'}],
                                                                                                             'default': None,
                                                                                                             'title': 'Observacao'},
                                                                                              'status': {'anyOf': [{'type': 'boolean'},
                                                                                                                   {'type': 'null'}],
                                                                                                         'default': None,
                                                                                                         'title': 'Status'}},
                                                                               'title': 'OutboundRequestDTO',
                                                                               'type': 'object'}}}},
                   'parameters': [{'name': 'id',
                                   'in': 'path',
                                   'required': True,
                                   'schema': {'type': 'integer', 'exclusiveMinimum': 0}}]}}

from datetime import date as Date, date as DateType, datetime as DateTimeType
from typing import Annotated, Optional, Literal
from fastapi import Query

class ListOutboundQueryDTO(InputDTO):
    date: Date | None = None

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from pydantic import Field, ConfigDict
from products.product_schema import ProductResponseDTO

class ItemOrderRequestDTO(BaseModel):
    product_id: int
    amount: Optional[int] = None
    kg: Optional[float] = None
    liters: Optional[float] = None

class ItemOrderResponseDTO(BaseModel):
    product_id: int
    name: str
    price: float = Field(alias="item_price")
    amount: Optional[int] = None
    kg: Optional[float] = None
    liters: Optional[float] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class OrderResponse(BaseModel):
    id: int
    status: bool
    total_value: float
    description: str | None = None
    date: datetime = Field(alias='order_date')
    items: List[ItemOrderResponseDTO] = Field(alias="item_order")

    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True
    )

class OrderRequestDTO(BaseModel):
    description: Optional[str] = None
    status: Optional[bool] = None
    total_value: Optional[float] = None
    order_date: Optional[date] = None
    client_id: Optional[int] = None  # cliente opcional vinculado à venda (CRM)
    payment_method: Optional[str] = None  # dinheiro | pix | cartao
    client_uuid: Optional[str] = None  # idempotência da venda offline (outbox)
    items: List[ItemOrderRequestDTO]


class ItemOrderResponseDTO2(BaseModel):
    prodcut: ProductResponseDTO
    price: float

    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True
    )

class OrderResponseDTO(BaseModel):
    id: int
    status: bool
    total_value: float
    description: str | None = None
    date: datetime = Field(alias='order_date')
    sale_point_id: int | None
    item_order: List[ItemOrderResponseDTO]

    model_config = ConfigDict(
        from_attributes=True, 
        populate_by_name=True
    )


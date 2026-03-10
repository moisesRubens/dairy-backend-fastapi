from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pydantic import Field, ConfigDict
from orders.order_schema import OrderResponseDTO

class SalePointResponseDTO(BaseModel):
    id: int | None
    name: str | None
    email: str | None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class SalePointRequestDTO(BaseModel):
    id: int | None = None
    name: str | None = None
    email: str | None = None
    password: str | None = None
    
class OrderSalePointResponseDTO(BaseModel):
    sale_point_id: int
    orders: List[OrderResponseDTO]
    
    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True
    )
    
class OutBoundRequestDTO(BaseModel):
    product_id: int
    name: str | None = None  
    status: bool | None = None
    date: Optional[datetime] = Field(default=None, alias="data")
    unit_type: Optional[str] = Field(default=None, alias="unidade")
    taken_quantity: float | None = None
    sold_quantity: float | None = None
    remaining_quantity: float | None = None
    total_value_item: Optional[float] = Field(default=None, alias="total_value")
    observation: Optional[str] = Field(default=None, alias="observacao")
    
    model_config = ConfigDict(
        populate_by_name=True
    )
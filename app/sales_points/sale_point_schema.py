from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pydantic import Field, ConfigDict
from orders.order_schema import OrderResponseDTO

class SalePointResponseDTO(BaseModel):
    id: int | None
    name: str | None
    email: str | None
    level: int | None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class SalePointRequestDTO(BaseModel):
    id: int | None = None
    name: str | None = None
    email: str | None = None
    password: str | None = None
    level: int | None = None
    
    
class OrderSalePointResponseDTO(BaseModel):
    sale_point_id: int
    orders: List[OrderResponseDTO]
    
    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True
    )
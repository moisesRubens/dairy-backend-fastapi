from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pydantic import Field, ConfigDict

class ItemOrderRequestDTO(BaseModel):
    product_id: int
    amount: Optional[int] = None
    kg: Optional[float] = None
    liters: Optional[float] = None

class ItemOrderResponseDTO(BaseModel):
    product_id: int
    price: float
    amount: Optional[int] = None
    kg: Optional[float] = None
    liters: Optional[float] = None

class OrderRequestDTO(BaseModel):
    description: Optional[str] = None
    items: List[ItemOrderRequestDTO]


class OrderResponseDTO(BaseModel):
    id: int
    status: bool
    total_value: float
    description: str
    date: datetime = Field(alias="order_date")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class SalePointResponseDTO(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True
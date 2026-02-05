from pydantic import BaseModel
from typing import List, Optional

class ItemOrderRequestDTO(BaseModel):
    product_id: int
    amount: Optional[int] = None
    kg: Optional[float] = None
    liters: Optional[float] = None

class OrderRequestDTO(BaseModel):
    description: Optional[str] = None
    items: List[ItemOrderRequestDTO]
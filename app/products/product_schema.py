from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pydantic import Field, ConfigDict

class ProductResponseDTO(BaseModel):
    id: int
    name: str
    price: float
    amount: int | None = None
    kg: int | None = None
    liters: int | None = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
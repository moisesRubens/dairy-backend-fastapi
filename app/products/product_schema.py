from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pydantic import Field, ConfigDict

class ProductResponseDTO(BaseModel):
    id: int
    name: str
    price: float
    amount: int | None = None
    kg: float | None = None
    liters: float | None = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class ItemRetiradaDTO(BaseModel):
    product_id: int
    quantidade: float
    unidade: str  

class RetirarProdutosRequestDTO(BaseModel):
    produtos: List[ItemRetiradaDTO]
    observacao: Optional[str] = None
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
    
class ItemToReturnToStorageDTO(BaseModel):
    product_id: int 
    
class ReturnToStorageRequestDTO(BaseModel):
    products: List[ItemToReturnToStorageDTO]

class RetirarProdutosRequestDTO(BaseModel):
    produtos: List[ItemRetiradaDTO]
    observacao: Optional[str] = None
    
class ItemsRetiradaResponseDTO(BaseModel):
    id: int
    sale_point_id: int
    product_id: int
    name: str  # Preenchido manualmente
    status: bool
    date: datetime = Field(alias="data")
    unit_type: str = Field(alias="unidade")
    taken_quantity: float
    sold_quantity: float
    remaining_quantity: float
    total_value_item: float = Field(alias="total_value")
    observation: Optional[str] = Field(alias="observacao")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    
    @classmethod
    def from_orm(cls, retirada):
        """Método para criar DTO a partir do modelo ORM"""
        return cls(
            id=retirada.id,
            sale_point_id=retirada.sale_point_id,
            product_id=retirada.product_id,
            name=retirada.product.name if retirada.product else None,
            status=retirada.status,
            date=retirada.data,
            unit_type=retirada.unidade,
            taken_quantity=retirada.taken_quantity,
            sold_quantity=retirada.sold_quantity,
            remaining_quantity=retirada.remaining_quantity, 
            total_value_item=retirada.total_value,
            observation=retirada.observacao
        )
    
class RetiradaResponseDTO(BaseModel):
    retirada_id: int
    observation: str | None = None
    List[ItemsRetiradaResponseDTO]
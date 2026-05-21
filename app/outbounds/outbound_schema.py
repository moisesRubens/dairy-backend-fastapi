from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from products.product_schema import ProductResponseDTO

class OutboundRequestDTO(BaseModel):
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
    
class OutboundResponseDTO(BaseModel):
    id: int
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
        from_attributes=True,
        populate_by_name=True
    )
    
class OutboundResponseDTOTest(BaseModel):
    id: int
    observation: Optional[str]  = Field(default=None, alias="observacao")
    date: Optional[datetime] = Field(default=None, alias="data")
    products: list[ProductResponseDTO]
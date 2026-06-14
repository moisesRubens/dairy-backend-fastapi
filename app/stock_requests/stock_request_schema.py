from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class StockRequestCreateDTO(BaseModel):
    """Payload do vendedor ao solicitar reposição para o próprio ponto."""
    product_id: int
    quantity: float
    unidade: str  # amount | kg | liters


class StockRequestRejectDTO(BaseModel):
    """Payload do admin ao recusar uma solicitação (motivo obrigatório)."""
    reason: str


class StockRequestResponseDTO(BaseModel):
    id: int
    requested_by_id: Optional[int] = None
    target_point_id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    unidade: str
    status: str
    reason: Optional[str] = None
    created_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    decided_by_id: Optional[int] = None
    applied_outbound_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

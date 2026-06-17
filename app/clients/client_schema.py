from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ClientCreateDTO(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdateDTO(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ClientResponseDTO(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    sale_point_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

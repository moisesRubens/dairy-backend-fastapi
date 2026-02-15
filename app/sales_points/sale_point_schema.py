from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pydantic import Field, ConfigDict

class SalePointResponseDTO(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


class SalePointRequestDTO(BaseModel):
    id: int | None = None
    name: str | None = None
    email: str | None = None
    password: str | None = None
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pydantic import Field, ConfigDict

class SalePointResponseDTO(BaseModel):
    id: int | None
    name: str | None
    email: str | None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class SalePointRequestDTO(BaseModel):
    id: int | None = None
    name: str | None = None
    email: str | None = None
    password: str | None = None
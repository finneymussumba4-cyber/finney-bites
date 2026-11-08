from pydantic import BaseModel, ConfigDict
from typing import Optional


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    image: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
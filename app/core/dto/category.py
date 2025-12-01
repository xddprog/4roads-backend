from datetime import datetime   
from uuid import UUID

from pydantic import BaseModel


class CategoryModel(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    image: str | None
    created_at: datetime
    updated_at: datetime
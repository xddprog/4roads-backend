from datetime import datetime   
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.utils.url_helper import get_absolute_url


class CategoryModel(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    image: str | None
    created_at: datetime
    updated_at: datetime

    @field_validator("image")
    @classmethod
    def validate_image(cls, value: str | None) -> str | None:
        return get_absolute_url(value)

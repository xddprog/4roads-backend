from pydantic import BaseModel, field_validator
from uuid import UUID

from app.core.dto.product import BaseProductModel
from app.utils.url_helper import get_absolute_url


class ReviewModel(BaseModel):
    id: UUID
    author_name: str
    content: str
    rating: int 
    image: str | None
    is_active: bool
    product_id: UUID
    product: BaseProductModel
    
    @field_validator("image")
    @classmethod
    def validate_image(cls, value: str | None) -> str | None:
        return get_absolute_url(value)

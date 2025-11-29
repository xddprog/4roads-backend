from pydantic import BaseModel
from uuid import UUID

from app.core.dto.product import BaseProductModel


class ReviewModel(BaseModel):
    id: UUID
    author_name: str
    content: str
    rating: int 
    image: str | None
    is_active: bool
    product_id: UUID
    product: BaseProductModel

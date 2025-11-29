from pydantic import BaseModel, ConfigDict, Field, field_validator
from uuid import UUID
from datetime import datetime

from app.utils.url_helper import get_absolute_url


class ProductImageModel(BaseModel):
    id: UUID
    image_path: str
    order: int
    
    @field_validator("image_path")
    @classmethod
    def validate_image_path(cls, value: str) -> str:
        return get_absolute_url(value)


class ProductCharacteristicModel(BaseModel):
    name: str
    value: str


class ProductModel(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    price: int
    old_price: int | None
    is_active: bool
    is_featured: bool
    category_id: UUID
    images: list[ProductImageModel]
    characteristics: list[ProductCharacteristicModel]

class BaseProductModel(BaseModel):
    id: UUID
    name: str
    slug: str
    updated_at: datetime
    is_active: bool


class ProductFilterModel(BaseModel):
    price_min: int | None = Field(None, description="Минимальная цена")
    price_max: int | None = Field(None, description="Максимальная цена")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "slug": "product-slug",
                "characteristics": {
                    "size": "XL",
                    "color": "red",
                },
                "limit": 20,
                "offset": 0
            }
        }
    )
    
    slug: str | None = Field(None, description="Фильтр по slug продукта")
    characteristics: dict[str, str] | None = Field(
        None,
        description="Словарь {characteristic_type_slug: value} для фильтрации по характеристикам"
    )
    limit: int = 20
    offset: int = 0
    category_ids: list[UUID] | None = Field(None, description="Фильтр по id категорий")
    
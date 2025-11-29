from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class ProductImageModel(BaseModel):
    id: UUID
    image_path: str
    order: int


class ProductCharacteristicModel(BaseModel):
    id: UUID
    value: str
    characteristic_type_id: UUID


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


class ProductFilterModel(BaseModel):
    """Модель для фильтрации продуктов"""
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

    
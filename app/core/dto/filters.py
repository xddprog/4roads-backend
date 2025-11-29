from pydantic import BaseModel
from uuid import UUID

from app.utils.enums import CharacteristicTypeEnum


class CategoryFilterModel(BaseModel):
    id: UUID
    name: str
    slug: str
    count: int


class CharacteristicFilterModel(BaseModel):
    name: CharacteristicTypeEnum
    slug: str
    values: list[str]


class AvailableFiltersModel(BaseModel):
    categories: list[CategoryFilterModel]
    characteristics: list[CharacteristicFilterModel]


from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_filter_service
from app.core.dto.filters import AvailableFiltersModel
from app.core.services.filter_service import FilterService


router = APIRouter()


@router.get(
    "/",
    response_model=AvailableFiltersModel,
    summary="Получить все доступные фильтры",
    description="Возвращает категории, материалы, размеры и цвета для фильтрации товаров"
)
async def get_available_filters(
    service: Annotated[FilterService, Depends(get_filter_service)]
) -> AvailableFiltersModel:
    return await service.get_available_filters()


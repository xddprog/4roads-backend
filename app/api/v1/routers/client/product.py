from typing import Annotated
from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_product_service
from app.core.dto.product import ProductModel, ProductFilterModel
from app.core.services.product_service import ProductService


router = APIRouter()


@router.post(
    "/all",
    summary="Получить список продуктов с фильтрацией",
    description="Возвращает список продуктов с возможностью фильтрации по slug и характеристикам"
)
async def get_products_filtered(
    filters: ProductFilterModel,
    service: Annotated[ProductService, Depends(get_product_service)]
) -> list[ProductModel]:
    return await service.get_filtered_products(filters)

from typing import Annotated
from fastapi import APIRouter, Depends, Header

from app.api.v1.dependencies import get_product_service
from app.core.dto.product import ProductModel, ProductFilterModel, BaseProductModel
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


@router.get(
    "/sitemap",
    summary="Получить все продукты для sitemap",
    description="Защищенный эндпоинт для получения id, slug, updated_at и is_active всех продуктов"
)
async def get_all_products_for_sitemap(
    service: Annotated[ProductService, Depends(get_product_service)],
    x_sitemap_password: Annotated[str | None, Header()] = None
) -> list[BaseProductModel]:
    return await service.get_all_for_sitemap(x_sitemap_password)


@router.get(
    "/{slug}",
    summary="Получить продукт по slug",
    description="Возвращает полную информацию о продукте"
)
async def get_product_by_slug(
    slug: str,
    service: Annotated[ProductService, Depends(get_product_service)]
) -> ProductModel:
    return await service.get_by_slug(slug)


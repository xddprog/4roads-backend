from typing import Annotated
from fastapi import APIRouter, Depends, Header, Query

from app.api.v1.dependencies import get_product_service
from app.core.dto.product import ProductModel, ProductFilterModel, BaseProductModel
from app.core.services.product_service import ProductService


router = APIRouter()


@router.get(
    "/search",
    response_model=list[ProductModel],
    summary="Поиск товаров по названию",
    description="Возвращает список товаров, название которых содержит поисковый запрос"
)
async def search_products(
    service: Annotated[ProductService, Depends(get_product_service)],
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    limit: int = Query(20, ge=1, le=100, description="Количество товаров"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации")
) -> list[ProductModel]:
    return await service.search_by_name(q, limit, offset)


@router.get(
    "/home",
    response_model=list[ProductModel],
    summary="Получить товары для главной страницы",
    description="Возвращает товары: новинки, рекомендуемые или скидки. Без флагов - просто первые товары"
)
async def get_home_products(
    service: Annotated[ProductService, Depends(get_product_service)],
    is_new: bool = Query(False, description="Новинки (последние добавленные)"),
    is_featured: bool = Query(False, description="Рекомендуемые (хиты продаж)"),
    is_sales: bool = Query(False, description="Скидки (товары с discount_percent)"),
    limit: int = Query(9, ge=1, le=50, description="Количество товаров")
) -> list[ProductModel]:
    return await service.get_for_home(is_new, is_featured, is_sales, limit)


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


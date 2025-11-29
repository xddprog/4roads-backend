from app.core.dto.product import ProductFilterModel, ProductModel, BaseProductModel
from app.core.repositories.product_repository import ProductRepository
from app.infrastructure.errors.base import NotFoundError
from app.infrastructure.errors.sitemap_errors import InvalidSitemapPassword
from app.infrastructure.config.config import APP_CONFIG


class ProductService:
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
    async def get_by_slug(self, slug: str) -> ProductModel:
        product = await self.repository.get_by_slug(slug)
        if not product:
            raise NotFoundError(f"Продукт с slug '{slug}' не найден")
        return ProductModel.model_validate(product, from_attributes=True)
    
    async def get_all_for_sitemap(self, password: str | None) -> list[BaseProductModel]:
        if not password or password != APP_CONFIG.SITEMAP_PASSWORD:
            raise InvalidSitemapPassword()
        
        products = await self.repository.get_all_items()
        return [
            BaseProductModel.model_validate(product, from_attributes=True)
            for product in products
        ]
    
    async def get_filtered_products(
        self,
        filters: ProductFilterModel
    ) -> list[ProductModel]:
        products = await self.repository.get_filtered_products(
            **filters.model_dump()
        )
        return [
            ProductModel.model_validate(product, from_attributes=True)
            for product in products
        ]


from app.core.dto.product import ProductFilterModel, ProductModel, BaseProductModel, ProductCharacteristicModel, ProductImageModel
from app.core.repositories.product_repository import ProductRepository
from app.infrastructure.errors.base import NotFoundError
from app.infrastructure.errors.sitemap_errors import InvalidSitemapPassword
from app.infrastructure.config.config import APP_CONFIG


class ProductService:
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
    def _convert_to_dto(self, product) -> ProductModel:
        """Преобразовать Product в ProductModel с правильными характеристиками"""
        return ProductModel(
            id=product.id,
            name=product.name,
            slug=product.slug,
            description=product.description,
            price=product.price,
            old_price=product.old_price,
            is_active=product.is_active,
            is_featured=product.is_featured,
            category_id=product.category_id,
            images=[
                ProductImageModel.model_validate(img, from_attributes=True)
                for img in sorted(product.images, key=lambda x: x.order)
            ],
            characteristics=[
                ProductCharacteristicModel(
                    name=char.characteristic_type.name,
                    value=char.value
                )
                for char in product.characteristics
            ]
        )
    
    async def get_by_slug(self, slug: str) -> ProductModel:
        product = await self.repository.get_by_slug(slug)
        if not product:
            raise NotFoundError(f"Продукт с slug '{slug}' не найден")
        return self._convert_to_dto(product)
    
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
        return [self._convert_to_dto(product) for product in products]
    
    async def get_for_home(
        self,
        is_new: bool = False,
        is_featured: bool = False,
        is_sales: bool = False,
        limit: int = 9
    ) -> list[ProductModel]:
        products = await self.repository.get_for_home(is_new, is_featured, is_sales, limit)
        return [self._convert_to_dto(product) for product in products]
    
    async def search_by_name(
        self,
        search_query: str,
        limit: int = 20,
        offset: int = 0
    ) -> list[ProductModel]:
        products = await self.repository.search_by_name(search_query, limit, offset)
        return [self._convert_to_dto(product) for product in products]

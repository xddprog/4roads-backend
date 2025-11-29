from app.core.dto.product import ProductFilterModel, ProductModel
from app.core.repositories.product_repository import ProductRepository


class ProductService:
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
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


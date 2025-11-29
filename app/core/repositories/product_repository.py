from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.repositories.base import SqlAlchemyRepository
from app.infrastructure.database.models.product import Product, ProductCharacteristic, CharacteristicType


class ProductRepository(SqlAlchemyRepository[Product]):
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Product)
    
    async def get_filtered_products(
        self,
        slug: str | None = None,
        characteristics: dict[str, str] | None = None,
        limit: int | None = None,
        offset: int | None = None
    ) -> list[Product]:
        
        query = (
            select(Product)
            .options(
                selectinload(Product.images),
                selectinload(Product.characteristics)
            )
        )
        
        if slug:
            query = query.where(Product.slug == slug)
        
        if characteristics:
            query = (
                query
                .join(ProductCharacteristic, Product.id == ProductCharacteristic.product_id)
                .join(CharacteristicType, ProductCharacteristic.characteristic_type_id == CharacteristicType.id)
            )
            
            conditions = []
            for char_slug, char_value in characteristics.items():
                conditions.append(
                    and_(
                        CharacteristicType.slug == char_slug,
                        ProductCharacteristic.value == char_value
                    )
                )
            
            query = query.where(or_(*conditions))
            
            query = (
                query
                .group_by(Product.id)
                .having(func.count(Product.id) >= len(characteristics))
            )
        
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def get_by_slug(self, slug: str) -> Product | None:
        query = (
            select(Product)
            .options(
                selectinload(Product.images),
                selectinload(Product.characteristics)
            )
            .where(Product.slug == slug)
        )
        result = await self.session.execute(query)
        return result.scalars().one_or_none()
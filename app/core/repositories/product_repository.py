from uuid import UUID
from sqlalchemy import and_, func, or_, select, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.repositories.base import SqlAlchemyRepository
from app.infrastructure.database.models.product import Product, ProductCharacteristic, CharacteristicType
from app.infrastructure.database.models.category import Category


class ProductRepository(SqlAlchemyRepository[Product]):
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Product)
    
    async def get_filtered_products(
        self,
        price_min: int | None = None,
        price_max: int | None = None,
        category_ids: list[UUID] | None = None,
        characteristics: dict[str, str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        slug: str | None = None,
    ) -> list[Product]:
        
        query = (
            select(Product)
            .options(
                selectinload(Product.images),
                selectinload(Product.characteristics).selectinload(ProductCharacteristic.characteristic_type)
            )
        )
        
        if category_ids:
            query = query.where(Product.category_id.in_(category_ids))
        
        if price_min:
            query = query.where(Product.price >= price_min)
        
        if price_max:
            query = query.where(Product.price <= price_max)
        
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
                selectinload(Product.characteristics).selectinload(ProductCharacteristic.characteristic_type)
            )
            .where(Product.slug == slug)
        )
        result = await self.session.execute(query)
        return result.scalars().one_or_none()
    
    async def get_for_home(
        self,
        is_new: bool = False,
        is_featured: bool = False,
        is_sales: bool = False,
        limit: int = 9
    ) -> list[Product]:
        query = (
            select(Product)
            .where(Product.is_active == True)
            .options(
                selectinload(Product.images),
                selectinload(Product.characteristics).selectinload(ProductCharacteristic.characteristic_type)
            )
            .limit(limit)
        )
        
        if is_new:
            query = query.order_by(Product.created_at.desc())
        elif is_featured:
            query = query.where(Product.is_featured == True).order_by(Product.created_at.desc())
        elif is_sales:
            query = query.where(Product.old_price != None).order_by(Product.created_at.desc())
        else:
            query = query.order_by(Product.created_at.desc())
        
        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_categories_with_count(self) -> list[tuple[Category, int]]:
        query = (
            select(Category, func.count(Product.id).label("product_count"))
            .join(Product, Category.id == Product.category_id)
            .where(Product.is_active == True)
            .group_by(Category.id)
        )
        result = await self.session.execute(query)
        return list(result.all())
    
    async def get_unique_characteristic_values(self, characteristic_type_slug: str) -> list[str]:
        query = (
            select(distinct(ProductCharacteristic.value))
            .join(CharacteristicType, ProductCharacteristic.characteristic_type_id == CharacteristicType.id)
            .join(Product, ProductCharacteristic.product_id == Product.id)
            .where(
                and_(
                    CharacteristicType.slug == characteristic_type_slug,
                    Product.is_active == True
                )
            )
            .order_by(ProductCharacteristic.value)
        )
        result = await self.session.execute(query)
        return [row[0] for row in result.all()]
    
    async def get_all_characteristic_values_grouped(self) -> dict[str, list[str]]:
        query = (
            select(
                CharacteristicType.slug,
                ProductCharacteristic.value
            )
            .join(ProductCharacteristic, CharacteristicType.id == ProductCharacteristic.characteristic_type_id)
            .join(Product, ProductCharacteristic.product_id == Product.id)
            .where(Product.is_active == True)
            .distinct()
            .order_by(CharacteristicType.slug, ProductCharacteristic.value)
        )
        
        result = await self.session.execute(query)
        
        grouped = {}
        for slug, value in result.all():
            if slug not in grouped:
                grouped[slug] = []
            grouped[slug].append(value)
        
        return grouped
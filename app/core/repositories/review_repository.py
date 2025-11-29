from sqlalchemy import select
from app.infrastructure.database.models.review import Review
from app.core.repositories.base import SqlAlchemyRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ReviewRepository(SqlAlchemyRepository[Review]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Review)

    async def get_all_items(self) -> list[Review]:
        query = select(Review).options(selectinload(Review.product))
        reviews = await self.session.execute(query)
        return reviews.scalars().all()
from app.infrastructure.database.models.category import Category
from app.core.repositories.base import SqlAlchemyRepository
from sqlalchemy.ext.asyncio import AsyncSession

class CategoryRepository(SqlAlchemyRepository[Category]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Category)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.base import SqlAlchemyRepository
from app.infrastructure.database.models.faq import FAQ


class FAQRepository(SqlAlchemyRepository[FAQ]):
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, FAQ)
from app.infrastructure.database.models.admin import Admin
from app.core.repositories.base import SqlAlchemyRepository
from sqlalchemy.ext.asyncio import AsyncSession

class AdminRepository(SqlAlchemyRepository[Admin]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Admin)
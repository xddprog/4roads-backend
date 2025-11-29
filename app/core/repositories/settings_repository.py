from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.base import SqlAlchemyRepository
from app.infrastructure.database.models.settings import Settings


class SettingsRepository(SqlAlchemyRepository[Settings]):
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Settings)



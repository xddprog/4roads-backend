from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.base import SqlAlchemyRepository
from app.infrastructure.database.models.product import CharacteristicType


class CharacteristicTypeRepository(SqlAlchemyRepository[CharacteristicType]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CharacteristicType)
    

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.infrastructure.config.config import DB_CONFIG
from app.infrastructure.database.models.base import Base
from app.utils.test_db import test_db

import app.infrastructure.database.events  # noqa: F401  # noqa: F401


class DatabaseConnection:
    def __init__(self):
        self._engine = create_async_engine(
            url=DB_CONFIG.get_url(is_async=True),
        )

    async def get_session(self) -> AsyncSession:
        return AsyncSession(bind=self._engine)
        
    async def init_test_db(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with await self.get_session() as session:
            await test_db(session)
        
    
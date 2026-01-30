from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.base import SqlAlchemyRepository
from app.infrastructure.database.models.order import Order


class OrderRepository(SqlAlchemyRepository[Order]):

    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    async def add_order(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        await self.session.refresh(order, attribute_names=["items"])
        return order

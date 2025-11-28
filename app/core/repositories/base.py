from typing import Any
from pydantic import UUID4
from sqlalchemy import Result, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import MappedColumn
from app.infrastructure.interfaces.repository import RepositoryInterface


class SqlAlchemyRepository[ModelType](RepositoryInterface[ModelType]):
    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    async def get_item(self, item_id: str) -> ModelType | None:
        item = await self.session.get(self.model, item_id)
        return item

    async def get_all_items(self, limit: int | None = None, offset: int | None = None) -> list[ModelType]:
        query = select(self.model)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        items = await self.session.execute(query)
        return items.scalars().all()

    async def get_by_filter(
        self, 
        *, 
        one_or_none: bool = False, 
        **filter_by: Any
    ) -> list[ModelType] | ModelType | None:
        query = select(self.model)
        
        for key, value in filter_by.items():
            query = query.where(getattr(self.model, key) == value)

        items = await self.session.execute(query)
        
        if one_or_none:
            return items.scalars().one_or_none()
        return items.scalars().all()

    async def add_item(self, **kwargs: Any) -> ModelType:
        item = self.model(**kwargs)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete_item(self, item: ModelType) -> None:
        await self.session.delete(item)
        await self.session.commit()

    async def update_item(self, item_id: str, **update_values: Any) -> ModelType:
        query = (
            update(self.model)
            .where(self.model.id == item_id)
            .values(update_values)
            .returning(self.model)
        )
        item: Result = await self.session.execute(query)
        item = item.scalars().all()[0]
        await self.session.commit()
        await self.session.refresh(item)
        return item

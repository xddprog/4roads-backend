import uuid
from sqlalchemy import UUID, select, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, column_property, deferred
from typing import TYPE_CHECKING

from app.infrastructure.database.models.base import Base
from app.infrastructure.database.models.product import Product



class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
            UUID(as_uuid=True), 
            primary_key=True, 
            default=uuid.uuid4
        )
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column( nullable=True)
    image: Mapped[str | None] = mapped_column(nullable=True)
    order: Mapped[int] = mapped_column(default=0, nullable=False)
    
    products: Mapped[list["Product"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan"
    )

    products_count: Mapped[int] = deferred(column_property(
        select(func.count())
        .select_from(Product)
        .where(
            Product.category_id == id
        )
        .correlate_except(Product)
        .scalar_subquery()
    ))

    def __repr__(self):
        return f"<Category(name='{self.name}', slug='{self.slug}')>"
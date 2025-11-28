from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.infrastructure.database.models.base import Base


if TYPE_CHECKING:
    from app.infrastructure.database.models.product import Product



class Category(Base):
    
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column( nullable=True)
    image: Mapped[str | None] = mapped_column(nullable=True)
    order: Mapped[int] = mapped_column(default=0, nullable=False)
    
    products: Mapped[list["Product"]] = relationship(
        "Product", 
        back_populates="category",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Category(name='{self.name}', slug='{self.slug}')>"
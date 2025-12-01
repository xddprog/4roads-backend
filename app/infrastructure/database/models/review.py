from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from uuid import UUID

from app.infrastructure.database.models.base import Base


if TYPE_CHECKING:
    from app.infrastructure.database.models.product import Product


class Review(Base):
    __tablename__ = "reviews"

    author_name: Mapped[str]
    content: Mapped[str]
    rating: Mapped[int] 
    image: Mapped[str | None]
    is_active: Mapped[bool] = mapped_column(default=True)
    
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    
    product: Mapped["Product"] = relationship(back_populates="reviews")

    def __repr__(self):
        return f"<Review(author='{self.author_name}', rating={self.rating})>"


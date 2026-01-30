from sqlalchemy import ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from uuid import UUID

from app.infrastructure.database.models.base import Base
from app.utils.enums import OrderStatusEnum


if TYPE_CHECKING:
    from app.infrastructure.database.models.product import Product


class Order(Base):
    __tablename__ = "orders"

    name: Mapped[str]
    phone: Mapped[str]
    email: Mapped[str | None]
    comment: Mapped[str | None]
    status: Mapped[OrderStatusEnum] = mapped_column(
        SQLEnum(OrderStatusEnum, native_enum=False, length=50),
        default=OrderStatusEnum.NEW,
    )
    total_amount: Mapped[int] = mapped_column(default=0)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"Order({self.id})"

    def __admin_repr__(self, request):
        return f"{self.name} ({self.phone})"


class OrderItem(Base):
    __tablename__ = "order_items"

    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    product_name: Mapped[str]
    unit_price: Mapped[int]
    quantity: Mapped[int]
    total_price: Mapped[int]

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()

    def __repr__(self):
        return f"{self.product_name} x{self.quantity}"

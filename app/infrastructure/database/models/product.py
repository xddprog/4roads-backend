from sqlalchemy import ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from uuid import UUID

from app.infrastructure.database.models.base import Base
from app.utils.enums import CharacteristicTypeEnum



if TYPE_CHECKING:
    from app.infrastructure.database.models.category import Category
    from app.infrastructure.database.models.review import Review


class Product(Base):
    __tablename__ = "products"

    name: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None]
    price: Mapped[int]
    discount_percent: Mapped[int | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_featured: Mapped[bool] = mapped_column(default=False)
    
    category_id: Mapped[UUID] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    
    category: Mapped["Category"] = relationship(back_populates="products")
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan"
    )
    characteristics: Mapped[list["ProductCharacteristic"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return self.name

    def __admin_repr__(self, request):
        return self.name


class ProductImage(Base):
    __tablename__ = "product_images"

    image_path: Mapped[str]
    order: Mapped[int] = mapped_column(default=0)
    
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))

    product: Mapped["Product"] = relationship(back_populates="images")

    def __repr__(self):
        return self.image_path


class CharacteristicType(Base):
    __tablename__ = "characteristic_types"

    name: Mapped[CharacteristicTypeEnum] = mapped_column(
        SQLEnum(CharacteristicTypeEnum, native_enum=False, length=50),
        unique=True
    )
    slug: Mapped[str] = mapped_column(unique=True)
    
    characteristics: Mapped[list["ProductCharacteristic"]] = relationship(
        back_populates="characteristic_type",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return self.name.value


class ProductCharacteristic(Base):
    __tablename__ = "product_characteristics"

    value: Mapped[str]
    
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    characteristic_type_id: Mapped[UUID] = mapped_column(ForeignKey("characteristic_types.id", ondelete="CASCADE"))
    
    product: Mapped["Product"] = relationship(back_populates="characteristics")
    characteristic_type: Mapped["CharacteristicType"] = relationship(back_populates="characteristics")

    def __repr__(self):
        type_name = "N/A"
        try:
            if self.characteristic_type and hasattr(self.characteristic_type, 'name'):
                type_name = self.characteristic_type.name.value if hasattr(self.characteristic_type.name, 'value') else str(self.characteristic_type.name)
        except (AttributeError, RuntimeError):
            pass
        return f"{type_name} - {self.value}"

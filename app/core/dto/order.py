from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.utils.enums import OrderStatusEnum


class OrderItemCreateModel(BaseModel):
    product_id: UUID
    quantity: int = Field(..., ge=1, le=999)


class OrderCreateModel(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    email: str | None = None
    comment: str | None = Field(None, max_length=1000)
    items: list[OrderItemCreateModel]

    @model_validator(mode="after")
    def validate_items(self) -> "OrderCreateModel":
        if not self.items:
            raise ValueError("Items list cannot be empty")
        return self


class OrderItemModel(BaseModel):
    id: UUID
    product_id: UUID | None
    product_name: str
    unit_price: int
    quantity: int
    total_price: int


class OrderModel(BaseModel):
    id: UUID
    name: str
    phone: str
    email: str | None
    comment: str | None
    status: OrderStatusEnum
    total_amount: int
    created_at: datetime
    items: list[OrderItemModel]

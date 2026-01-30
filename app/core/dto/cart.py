from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class CartItemUpdateModel(BaseModel):
    product_id: UUID
    quantity: int = Field(..., ge=1, le=999)


class CartItemModel(BaseModel):
    product_id: UUID
    name: str
    unit_price: int
    quantity: int
    total_price: int


class CartModel(BaseModel):
    items: list[CartItemModel]
    total_amount: int


class CheckoutModel(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    email: str | None = None
    comment: str | None = Field(None, max_length=1000)


class CartItemSetModel(BaseModel):
    quantity: int = Field(..., ge=0, le=999)


class CartStateModel(BaseModel):
    items: dict[UUID, int]

    @model_validator(mode="after")
    def validate_items(self) -> "CartStateModel":
        if not self.items:
            return self
        for qty in self.items.values():
            if qty < 1:
                raise ValueError("Quantity must be >= 1")
        return self

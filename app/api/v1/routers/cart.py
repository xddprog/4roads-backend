from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_db_session, get_order_service
from app.core.dto.cart import (
    CartItemModel,
    CartItemSetModel,
    CartItemUpdateModel,
    CartModel,
    CheckoutModel,
)
from app.core.dto.order import OrderCreateModel, OrderItemCreateModel, OrderModel
from app.core.repositories.product_repository import ProductRepository
from app.core.services.order_service import OrderService


router = APIRouter()

SESSION_CART_KEY = "cart"


def _get_cart(request: Request) -> dict[str, int]:
    raw = request.session.get(SESSION_CART_KEY)
    if not isinstance(raw, dict):
        raw = {}
        request.session[SESSION_CART_KEY] = raw
    return raw


def _save_cart(request: Request, cart: dict[str, int]) -> None:
    request.session[SESSION_CART_KEY] = cart


def _clean_cart(cart: dict[str, int]) -> dict[str, int]:
    cleaned = {}
    for key, qty in cart.items():
        if not isinstance(key, str):
            continue
        if not isinstance(qty, int):
            continue
        if qty < 1:
            continue
        cleaned[key] = qty
    return cleaned


async def _build_cart_response(
    request: Request,
    repo: ProductRepository,
) -> CartModel:
    cart = _clean_cart(_get_cart(request))
    if not cart:
        _save_cart(request, {})
        return CartModel(items=[], total_amount=0)

    ids: list[UUID] = []
    for key in cart.keys():
        try:
            ids.append(UUID(key))
        except ValueError:
            continue

    products = await repo.get_by_ids(ids)
    product_map = {product.id: product for product in products}

    items: list[CartItemModel] = []
    total_amount = 0
    updated_cart: dict[str, int] = {}

    for key, qty in cart.items():
        try:
            product_id = UUID(key)
        except ValueError:
            continue
        product = product_map.get(product_id)
        if not product:
            continue
        total_price = product.price * qty
        total_amount += total_price
        items.append(
            CartItemModel(
                product_id=product.id,
                name=product.name,
                unit_price=product.price,
                quantity=qty,
                total_price=total_price,
            )
        )
        updated_cart[key] = qty

    _save_cart(request, updated_cart)
    return CartModel(items=items, total_amount=total_amount)


@router.get(
    "/",
    response_model=CartModel,
    summary="Получить корзину",
    description="Возвращает корзину без авторизации (cookie-based session)",
)
async def get_cart(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CartModel:
    repo = ProductRepository(session)
    return await _build_cart_response(request, repo)


@router.post(
    "/items",
    response_model=CartModel,
    status_code=status.HTTP_200_OK,
    summary="Добавить товар в корзину",
)
async def add_item(
    payload: CartItemUpdateModel,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CartModel:
    repo = ProductRepository(session)
    products = await repo.get_by_ids([payload.product_id])
    if not products:
        raise HTTPException(status_code=404, detail="Товар не найден")

    cart = _clean_cart(_get_cart(request))
    key = str(payload.product_id)
    cart[key] = cart.get(key, 0) + payload.quantity
    _save_cart(request, cart)

    return await _build_cart_response(request, repo)


@router.patch(
    "/items/{product_id}",
    response_model=CartModel,
    summary="Изменить количество товара",
)
async def set_item_quantity(
    product_id: UUID,
    payload: CartItemSetModel,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CartModel:
    repo = ProductRepository(session)
    cart = _clean_cart(_get_cart(request))
    key = str(product_id)

    if key not in cart:
        raise HTTPException(status_code=404, detail="Товара нет в корзине")

    if payload.quantity == 0:
        cart.pop(key, None)
    else:
        cart[key] = payload.quantity

    _save_cart(request, cart)
    return await _build_cart_response(request, repo)


@router.delete(
    "/items/{product_id}",
    response_model=CartModel,
    summary="Удалить товар из корзины",
)
async def remove_item(
    product_id: UUID,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CartModel:
    repo = ProductRepository(session)
    cart = _clean_cart(_get_cart(request))
    key = str(product_id)

    if key not in cart:
        raise HTTPException(status_code=404, detail="Товара нет в корзине")

    cart.pop(key, None)
    _save_cart(request, cart)
    return await _build_cart_response(request, repo)


@router.delete(
    "/",
    response_model=CartModel,
    summary="Очистить корзину",
)
async def clear_cart(
    request: Request,
) -> CartModel:
    _save_cart(request, {})
    return CartModel(items=[], total_amount=0)


@router.post(
    "/checkout",
    response_model=OrderModel,
    status_code=status.HTTP_201_CREATED,
    summary="Оформить заказ",
    description="Создаёт заказ из корзины и очищает её",
)
async def checkout(
    payload: CheckoutModel,
    request: Request,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderModel:
    cart = _clean_cart(_get_cart(request))
    if not cart:
        raise HTTPException(status_code=400, detail="Корзина пуста")

    items = [
        OrderItemCreateModel(product_id=UUID(key), quantity=qty)
        for key, qty in cart.items()
    ]

    order_payload = OrderCreateModel(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        comment=payload.comment,
        items=items,
    )

    order = await service.create_order(order_payload)
    _save_cart(request, {})
    return order

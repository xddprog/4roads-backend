import asyncio
from fastapi import BackgroundTasks

from app.core.dto.order import OrderCreateModel, OrderModel
from app.core.dto.settings import SettingsModel
from app.core.repositories.order_repository import OrderRepository
from app.core.repositories.product_repository import ProductRepository
from app.core.repositories.settings_repository import SettingsRepository
from app.infrastructure.database.models.order import Order, OrderItem
from app.infrastructure.email.sender import send_order_notification
from app.infrastructure.errors.base import NotFoundError
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class OrderService:

    def __init__(
        self,
        repository: OrderRepository,
        product_repository: ProductRepository,
        settings_repository: SettingsRepository,
    ):
        self.repository = repository
        self.product_repository = product_repository
        self.settings_repository = settings_repository

    async def create_order(
        self,
        data: OrderCreateModel,
        background_tasks: BackgroundTasks | None = None,
    ) -> OrderModel:
        product_ids = [item.product_id for item in data.items]
        products = await self.product_repository.get_by_ids(product_ids)
        product_map = {product.id: product for product in products}

        missing_ids = [
            str(item.product_id)
            for item in data.items
            if item.product_id not in product_map
        ]
        if missing_ids:
            raise NotFoundError(f"Товары не найдены: {', '.join(missing_ids)}")

        total_amount = 0
        order_items: list[OrderItem] = []
        for item in data.items:
            product = product_map[item.product_id]
            unit_price = product.price
            total_price = unit_price * item.quantity
            total_amount += total_price
            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=unit_price,
                    quantity=item.quantity,
                    total_price=total_price,
                )
            )

        order = Order(
            name=data.name,
            phone=data.phone,
            email=data.email,
            comment=data.comment,
            total_amount=total_amount,
            items=order_items,
        )

        created = await self.repository.add_order(order)
        order_model = OrderModel.model_validate(created, from_attributes=True)

        settings = await self._get_settings_safe()
        if settings:
            if background_tasks:
                background_tasks.add_task(send_order_notification, settings, order_model)
            else:
                asyncio.create_task(send_order_notification(settings, order_model))

        return order_model

    async def _get_settings_safe(self) -> SettingsModel | None:
        try:
            settings_list = await self.settings_repository.get_all_items()
        except Exception as exc:
            logger.error("settings_fetch_failed", error=str(exc))
            return None

        if not settings_list:
            return None

        return SettingsModel.model_validate(settings_list[0], from_attributes=True)

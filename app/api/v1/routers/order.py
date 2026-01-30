from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api.v1.dependencies import get_order_service
from app.core.dto.order import OrderCreateModel, OrderModel
from app.core.services.order_service import OrderService


router = APIRouter()


@router.post(
    "/",
    response_model=OrderModel,
    status_code=status.HTTP_201_CREATED,
    summary="Создать заказ",
    description="Создаёт заказ (заявку) без авторизации",
)
async def create_order(
    data: OrderCreateModel,
    background_tasks: BackgroundTasks,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderModel:
    return await service.create_order(data, background_tasks=background_tasks)

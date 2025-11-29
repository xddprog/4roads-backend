from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_review_service
from app.core.dto.review import ReviewModel
from app.core.services.review_service import ReviewService


router = APIRouter()


@router.get(
    "/all",
    summary="Получить все отзывы",
    description="Получение всех отзывов"
)
async def get_all_reviews(
    service: Annotated[ReviewService, Depends(get_review_service)]
) -> list[ReviewModel]:
    return await service.get_all_reviews()
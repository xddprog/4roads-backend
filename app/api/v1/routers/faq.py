from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_faq_service
from app.core.dto.faq import FAQModel
from app.core.services.faq_service import FAQService


router = APIRouter()


@router.get(
    "/",
    response_model=list[FAQModel],
    summary="Получить список FAQ",
    description="Возвращает список активных часто задаваемых вопросов"
)
async def get_faqs(
    service: Annotated[FAQService, Depends(get_faq_service)]
) -> list[FAQModel]:
    return await service.get_faqs()


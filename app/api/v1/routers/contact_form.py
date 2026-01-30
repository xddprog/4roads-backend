from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api.v1.dependencies import get_contact_form_service
from app.core.dto.contact_form import ContactFormCreateModel, ContactFormModel
from app.core.services.contact_form_service import ContactFormService


router = APIRouter()


@router.post(
    "/",
    response_model=ContactFormModel,
    status_code=status.HTTP_201_CREATED,
    summary="Отправить заявку",
    description="Создаёт новую заявку обратной связи"
)
async def create_contact_form(
    data: ContactFormCreateModel,
    background_tasks: BackgroundTasks,
    service: Annotated[ContactFormService, Depends(get_contact_form_service)]
) -> ContactFormModel:
    return await service.create_contact_form(data, background_tasks=background_tasks)

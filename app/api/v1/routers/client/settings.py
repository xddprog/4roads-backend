from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_settings_service
from app.core.dto.settings import SettingsModel
from app.core.services.settings_service import SettingsService
from app.infrastructure.errors.base import NotFoundError
from app.utils.error_extra import error_response


router = APIRouter()


@router.get(
    "/",
    response_model=SettingsModel,
    responses={**error_response(NotFoundError)},
    summary="Получить настройки сайта",
    description="Возвращает контактную информацию, социальные сети, время работы и описание компании"
)
async def get_settings(
    settings_service: Annotated[SettingsService, Depends(get_settings_service)]
) -> SettingsModel:
    return await settings_service.get_settings()
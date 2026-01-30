from app.core.dto.settings import SettingsModel
from app.core.repositories.settings_repository import SettingsRepository
from app.infrastructure.errors.base import InternalServerError, NotFoundError


class SettingsService:
    def __init__(self, repository: SettingsRepository):
        self.repository = repository
    
    async def get_settings(self) -> SettingsModel:
        settings = await self.repository.get_all_items()
        
        if not settings:
            raise NotFoundError("Настройки сайта не найдены")

        settings = settings[0]
        try:
            return SettingsModel.model_validate(settings, from_attributes=True)
        except Exception as exc:
            raise InternalServerError(f"Ошибка в настройках сайта: {exc}") from exc

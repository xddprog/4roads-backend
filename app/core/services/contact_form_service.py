import asyncio
from fastapi import BackgroundTasks

from app.core.dto.contact_form import ContactFormCreateModel, ContactFormModel
from app.core.dto.settings import SettingsModel
from app.core.repositories.contact_form_repository import ContactFormRepository
from app.core.repositories.settings_repository import SettingsRepository
from app.infrastructure.email.sender import send_contact_form_notification
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ContactFormService:
    
    def __init__(self, repository: ContactFormRepository, settings_repository: SettingsRepository):
        self.repository = repository
        self.settings_repository = settings_repository
    
    async def create_contact_form(
        self,
        data: ContactFormCreateModel,
        background_tasks: BackgroundTasks | None = None
    ) -> ContactFormModel:
        created = await self.repository.add_item(**data.model_dump())
        contact = ContactFormModel.model_validate(created, from_attributes=True)

        settings = await self._get_settings_safe()
        if settings:
            if background_tasks:
                background_tasks.add_task(send_contact_form_notification, settings, contact)
            else:
                asyncio.create_task(send_contact_form_notification(settings, contact))

        return contact

    async def _get_settings_safe(self) -> SettingsModel | None:
        try:
            settings_list = await self.settings_repository.get_all_items()
        except Exception as exc:
            logger.error("settings_fetch_failed", error=str(exc))
            return None

        if not settings_list:
            return None

        return SettingsModel.model_validate(settings_list[0], from_attributes=True)

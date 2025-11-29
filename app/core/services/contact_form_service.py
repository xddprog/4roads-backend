from app.core.dto.contact_form import ContactFormCreateModel, ContactFormModel
from app.core.repositories.contact_form_repository import ContactFormRepository
from app.infrastructure.database.models.contact_form import ContactForm


class ContactFormService:
    
    def __init__(self, repository: ContactFormRepository):
        self.repository = repository
    
    async def create_contact_form(self, data: ContactFormCreateModel) -> ContactFormModel:
        created = await self.repository.add_item(**data.model_dump())
        return ContactFormModel.model_validate(created, from_attributes=True)

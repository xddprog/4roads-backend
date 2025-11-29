from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.base import SqlAlchemyRepository
from app.infrastructure.database.models.contact_form import ContactForm


class ContactFormRepository(SqlAlchemyRepository[ContactForm]):
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ContactForm)


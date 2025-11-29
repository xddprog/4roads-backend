from app.core.dto.faq import FAQModel
from app.core.repositories.faq_repository import FAQRepository


class FAQService:
    
    def __init__(self, repository: FAQRepository):
        self.repository = repository
    
    async def get_faqs(self) -> list[FAQModel]:
        faqs = await self.repository.get_all_items()
        return [FAQModel.model_validate(faq, from_attributes=True) for faq in faqs]

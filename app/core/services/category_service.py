from app.core.repositories.category_repository import CategoryRepository
from app.core.dto.category import CategoryModel

class CategoryService:
    def __init__(self, repository: CategoryRepository):
        self.repository = repository

    async def get_all_categories(self) -> list[CategoryModel]:
        categories = await self.repository.get_all_items()
        return [CategoryModel.model_validate(category, from_attributes=True) for category in categories]
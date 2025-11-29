from app.core.repositories.review_repository import ReviewRepository
from app.core.dto.review import ReviewModel


class ReviewService:
    
    def __init__(self, repository: ReviewRepository):
        self.repository = repository
    
    async def get_all_reviews(self) -> list[ReviewModel]:
        reviews = await self.repository.get_all_items()
        return [ReviewModel.model_validate(review, from_attributes=True) for review in reviews]
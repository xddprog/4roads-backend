from app.core.dto.filters import AvailableFiltersModel, CategoryFilterModel, CharacteristicFilterModel
from app.core.repositories.product_repository import ProductRepository
from app.core.repositories.characteristic_repository import CharacteristicTypeRepository


class FilterService:
    def __init__(
        self, 
        product_repository: ProductRepository,
        characteristic_repository: CharacteristicTypeRepository
    ):
        self.product_repository = product_repository
        self.characteristic_repository = characteristic_repository
    
    async def get_available_filters(self) -> AvailableFiltersModel:
        categories_data = await self.product_repository.get_categories_with_count()
        categories = [
            CategoryFilterModel(
                id=category.id,
                name=category.name,
                slug=category.slug,
                count=count
            )
            for category, count in categories_data
        ]
        
        characteristic_types = await self.characteristic_repository.get_all_items()
        
        values_grouped = await self.product_repository.get_all_characteristic_values_grouped()
        
        characteristics = []
        for char_type in characteristic_types:
            values = values_grouped.get(char_type.slug, [])
            if values:
                characteristics.append(
                    CharacteristicFilterModel(
                        name=char_type.name.value,
                        slug=char_type.slug,
                        values=values
                    )
                )
        
        return AvailableFiltersModel(
            categories=categories,
            characteristics=characteristics
        )


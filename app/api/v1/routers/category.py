from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.services.category_service import CategoryService
from app.api.v1.dependencies import get_category_service
from app.core.dto.category import CategoryModel

router = APIRouter()


@router.get("/all")
async def get_all_categories(
    category_service: Annotated[CategoryService, Depends(get_category_service)]
) -> list[CategoryModel]:
    return await category_service.get_all_categories()

    
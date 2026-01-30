from typing import Annotated, AsyncGenerator

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dto.admin import BaseAdminModel
import app.core.repositories as repositories
import app.core.services as services


token_scheme = HTTPBearer(auto_error=False)


async def get_db_session(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    session = await request.app.state.db_connection.get_session()
    try:
        yield session
    finally:
        await session.close()


async def get_settings_service(session=Depends(get_db_session)) -> services.SettingsService:
    return services.SettingsService(
        repository=repositories.SettingsRepository(session=session)
    )


async def get_contact_form_service(session=Depends(get_db_session)) -> services.ContactFormService:
    return services.ContactFormService(
        repository=repositories.ContactFormRepository(session=session),
        settings_repository=repositories.SettingsRepository(session=session)
    )


async def get_faq_service(session=Depends(get_db_session)) -> services.FAQService:
    return services.FAQService(
        repository=repositories.FAQRepository(session=session)
    )


async def get_product_service(session=Depends(get_db_session)) -> services.ProductService:
    return services.ProductService(
        repository=repositories.ProductRepository(session=session)
    )


async def get_review_service(session=Depends(get_db_session)) -> services.ReviewService:
    return services.ReviewService(
        repository=repositories.ReviewRepository(session=session)
    )


async def get_filter_service(session=Depends(get_db_session)) -> services.FilterService:
    return services.FilterService(
        product_repository=repositories.ProductRepository(session=session),
        characteristic_repository=repositories.CharacteristicTypeRepository(session=session)
    )


async def get_category_service(session=Depends(get_db_session)) -> services.CategoryService:
    return services.CategoryService(
        repository=repositories.CategoryRepository(session=session)
    )

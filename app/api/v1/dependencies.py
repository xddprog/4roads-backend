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


async def get_auth_service(session=Depends(get_db_session)) -> services.AuthService:
    return services.AuthService(
        repository=repositories.AdminRepository(session=session)
    )


async def get_current_admin_dependency(
    auth_service: Annotated[services.AuthService, Depends(get_auth_service)],
    auth_scheme: Annotated[HTTPAuthorizationCredentials | None, Depends(token_scheme)]
) -> BaseAdminModel:
    token = auth_scheme.credentials if auth_scheme else None
    token_data = await auth_service.verify_token(token)
    return await auth_service.check_user_exist(token_data)


async def get_settings_service(session=Depends(get_db_session)) -> services.SettingsService:
    return services.SettingsService(
        repository=repositories.SettingsRepository(session=session)
    )


async def get_contact_form_service(session=Depends(get_db_session)) -> services.ContactFormService:
    return services.ContactFormService(
        repository=repositories.ContactFormRepository(session=session)
    )


async def get_faq_service(session=Depends(get_db_session)) -> services.FAQService:
    return services.FAQService(
        repository=repositories.FAQRepository(session=session)
    )

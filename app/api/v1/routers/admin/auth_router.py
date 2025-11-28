from typing import Annotated
from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_auth_service, get_current_admin_dependency
from app.core.dto.auth import AuthUserModel, TokenModel, RefreshTokenModel
from app.core.dto.admin import BaseAdminModel
from app.core.services.auth_service import AuthService
from app.infrastructure.errors.auth_errors import AccessDenied, InvalidCredentials
from app.utils.error_extra import error_response


router = APIRouter()


@router.post(
    "/login",
    responses={**error_response(InvalidCredentials)}
)
async def login(
    form: AuthUserModel, 
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> TokenModel:
    """
    Аутентификация пользователя и выдача JWT-токена.

    Принимает логин и пароль. Если учетные данные верны, возвращает
    access-токен, который необходимо использовать в заголовке
    Authorization: Bearer <token> для доступа к защищенным методам.

    Args:
        form (AuthUserModel): Данные для входа (login, password).

    Returns:
        TokenModel: Объект с JWT-токеном и типом токена (bearer).
    
    Raises:
        InvalidCredentials (401): Если логин или пароль неверны.
    """
    return await auth_service.login_user(form)


@router.post(
    "/refresh",
    responses={**error_response(InvalidCredentials), **error_response(AccessDenied)}
)
async def refresh_token(
    request: RefreshTokenModel,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> TokenModel:
    """
    Обновление access токена с помощью refresh токена.

    Принимает refresh токен и возвращает новую пару токенов (access и refresh).
    Используется когда access токен истек.

    Args:
        request (RefreshTokenRequest): Объект с refresh токеном.

    Returns:
        TokenModel: Новая пара токенов (access и refresh).
    
    Raises:
        InvalidCredentials (401): Если refresh токен невалиден или истек.
        AccessDenied (403): Если пользователь не найден.
    """
    return await auth_service.refresh_access_token(request.refresh_token)


@router.get(
    "/current-user",
    responses={**error_response(AccessDenied), **error_response(InvalidCredentials)},
)
async def current_user(
    current_user: Annotated[BaseAdminModel, Depends(get_current_admin_dependency)]
) -> BaseAdminModel:
   
    return current_user
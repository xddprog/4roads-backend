from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi.security import HTTPAuthorizationCredentials
import jwt
from passlib.context import CryptContext

from app.core.dto.admin import BaseAdminModel
from app.core.dto.auth import AuthUserModel, TokenModel
from app.core.repositories.admin_repository import AdminRepository
from app.infrastructure.config.config import JWT_CONFIG
from app.infrastructure.database.models.admin import Admin
from app.infrastructure.errors.auth_errors import AccessDenied, InvalidCredentials


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class AuthService:
    def __init__(self, repository: AdminRepository):
        self.repository = repository

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def _create_access_token(self, admin: Admin) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_CONFIG.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": str(admin.id), "type": "access", "exp": expire}
        encoded_jwt = jwt.encode(to_encode, JWT_CONFIG.SECRET_KEY, algorithm=JWT_CONFIG.ALGORITHM)
        return encoded_jwt
    
    def _create_refresh_token(self, admin: Admin) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=JWT_CONFIG.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {"sub": str(admin.id), "type": "refresh", "exp": expire}
        encoded_jwt = jwt.encode(to_encode, JWT_CONFIG.SECRET_KEY, algorithm=JWT_CONFIG.ALGORITHM)
        return encoded_jwt

    async def login_user(self, form: AuthUserModel) -> TokenModel:
        admin = await self.repository.get_by_filter(login=form.login, one_or_none=True)
        if not admin or not self._verify_password(form.password, admin.password):
            raise InvalidCredentials()

        access_token = self._create_access_token(admin)
        refresh_token = self._create_refresh_token(admin)
        return TokenModel(access_token=access_token, refresh_token=refresh_token)

    async def verify_token(self, token: str | None) -> dict:
        if not token:
            raise AccessDenied()

        try:
            payload = jwt.decode(token, JWT_CONFIG.SECRET_KEY, algorithms=[JWT_CONFIG.ALGORITHM])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise InvalidCredentials()

    async def check_user_exist(self, token_data: dict) -> BaseAdminModel:
        try:
            user_id = UUID(token_data.get("sub"))
        except (ValueError, TypeError):
            raise InvalidCredentials()

        admin = await self.repository.get_by_filter(id=user_id, one_or_none=True)
        if not admin:
            raise AccessDenied()
        return BaseAdminModel.model_validate(admin, from_attributes=True)
    
    async def refresh_access_token(self, refresh_token: str) -> TokenModel:
        """Обновить access токен используя refresh токен"""
        token_data = await self.verify_token(refresh_token)
        
        if token_data.get("type") != "refresh":
            raise InvalidCredentials()
        
        try:
            user_id = UUID(token_data.get("sub"))
        except (ValueError, TypeError):
            raise InvalidCredentials()
        
        admin = await self.repository.get_by_filter(id=user_id, one_or_none=True)
        if not admin:
            raise AccessDenied()
        
        new_access_token = self._create_access_token(admin)
        new_refresh_token = self._create_refresh_token(admin)
        
        return TokenModel(access_token=new_access_token, refresh_token=new_refresh_token)
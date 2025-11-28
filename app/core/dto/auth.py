from pydantic import BaseModel


class AuthUserModel(BaseModel):
    login: str
    password: str


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str


class RefreshTokenModel(BaseModel):
    refresh_token: str
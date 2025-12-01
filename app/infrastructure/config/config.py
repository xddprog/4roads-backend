from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Определить корень проекта (где находится .env)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        case_sensitive=True,
        extra="ignore",
        env_nested_delimiter="__"
    )


class DatabaseConfig(Config):
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    
    def get_url(self, is_async: bool = True) -> str:
        user, password, host, port, db = (
            self.DB_USER, self.DB_PASS, 
            self.DB_HOST, self.DB_PORT, self.DB_NAME
        )
        
        driver = "postgresql+asyncpg" if is_async else "postgresql"
        return f"{driver}://{user}:{password}@{host}:{port}/{db}"


class JWTConfig(Config):
    
    SECRET_KEY: str = Field(default="change-me-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=3)


class AppConfig(Config):
    APP_NAME: str = Field(default="4roads API")
    DEBUG: bool = Field(default=False)
    STATIC_URL: str = Field(default="http://localhost:8000/static")
    
    STATIC_DIR: str = Field(default="static")
    IMAGES_DIR: str = Field(default="static/images")
    
    MAX_IMAGE_SIZE_MB: int = Field(default=10)
    WEBP_QUALITY: int = Field(default=85)
    
    SLOW_REQUEST_THRESHOLD: float = Field(default=1.0, description="Порог медленных запросов в секундах")

    CORS_ALLOWED_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:5173")
    
    SITEMAP_PASSWORD: str = Field(default="change-me-sitemap-secret")


class Settings(Config):
    
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    jwt: JWTConfig = Field(default_factory=JWTConfig)
    app: AppConfig = Field(default_factory=AppConfig)


settings = Settings()

DB_CONFIG = settings.database
JWT_CONFIG = settings.jwt
APP_CONFIG = settings.app

from app.infrastructure.config.config import APP_CONFIG


def get_absolute_url(path: str) -> str:
    if not path:
        return None
    return f"{APP_CONFIG.STATIC_URL}/images/{path}"
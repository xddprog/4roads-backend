from sqlalchemy import create_engine
from app.infrastructure.config.config import DB_CONFIG

sync_engine = create_engine(DB_CONFIG.get_url(is_async=False))

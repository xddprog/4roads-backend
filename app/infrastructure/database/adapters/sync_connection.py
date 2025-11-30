from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.config.config import DB_CONFIG

sync_engine = create_engine(DB_CONFIG.get_url(is_async=False))
sync_session_maker = sessionmaker(bind=sync_engine, expire_on_commit=False)

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON

from app.infrastructure.database.models.base import Base


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    phone: Mapped[str | None]
    email: Mapped[str | None]
    address: Mapped[str | None]
    
    vk_url: Mapped[str | None]
    telegram_url: Mapped[str | None]
    whatsapp_url: Mapped[str | None]
    youtube_url: Mapped[str | None]
    
    about_text: Mapped[str | None]
    
    # Время работы (JSON: {"weekdays": {"start": "09:00", "end": "18:00"}, "weekend": {...}, "note": "..."})
    work_hours: Mapped[dict | None] = mapped_column(JSON)
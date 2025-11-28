from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import Base


class FAQ(Base):
    __tablename__ = "faqs"
    
    question: Mapped[str]
    answer: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)

    
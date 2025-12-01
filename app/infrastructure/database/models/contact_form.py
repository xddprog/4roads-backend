from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import Base


class ContactForm(Base):
    __tablename__ = "contact_forms"

    name: Mapped[str]
    phone: Mapped[str]
    message: Mapped[str]
    
    is_processed: Mapped[bool] = mapped_column(default=False)

    def __repr__(self):
        return f"<ContactForm(name='{self.name}', phone='{self.phone}', processed={self.is_processed})>"


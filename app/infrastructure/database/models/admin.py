from app.infrastructure.database.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column

class Admin(Base):
    __tablename__ = "admins"

    login: Mapped[str] = mapped_column(unique=True, index=True)
    password: Mapped[str]

    def __repr__(self):
        return f"<Admin(login='{self.login}')>"
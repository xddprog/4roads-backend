
from pydantic import BaseModel
from uuid import UUID


class BaseAdminModel(BaseModel):
    id: UUID
    login: str

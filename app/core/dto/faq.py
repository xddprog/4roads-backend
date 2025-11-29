from pydantic import BaseModel, ConfigDict
from uuid import UUID


class FAQModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    question: str
    answer: str


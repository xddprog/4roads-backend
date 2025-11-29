from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime


class ContactFormCreateModel(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    message: str = Field(..., min_length=25, max_length=1000)


class ContactFormModel(BaseModel):    
    id: UUID
    name: str
    phone: str
    message: str
    is_processed: bool
    created_at: datetime


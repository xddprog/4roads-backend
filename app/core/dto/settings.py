import json

from pydantic import BaseModel, ConfigDict, field_validator


class TimeRange(BaseModel):
    start: str 
    end: str    


class WorkHoursData(BaseModel):
    weekdays: TimeRange | None = None
    weekend: TimeRange | None = None
    note: str | None = None


class SettingsModel(BaseModel):
    id: int
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    vk_url: str | None = None
    telegram_url: str | None = None
    whatsapp_url: str | None = None
    youtube_url: str | None = None
    about_text: str | None = None
    work_hours: WorkHoursData | None = None

    @field_validator("work_hours", mode="before")
    @classmethod
    def parse_work_hours(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                return json.loads(text)
            except Exception:
                return None
        return value

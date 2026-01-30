from pydantic import BaseModel, ConfigDict


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

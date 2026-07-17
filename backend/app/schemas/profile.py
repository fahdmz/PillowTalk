from typing import Literal, Optional

from pydantic import BaseModel

Language = Literal["en", "id"]
FactorLevel = Literal["low", "medium", "high"]


class ProfileOut(BaseModel):
    id: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    language: Language = "en"
    bedtime_mode: bool = False
    reminder_tone: str = "chimes"
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:00"


class ProfilePatch(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    language: Optional[Language] = None
    bedtime_mode: Optional[bool] = None
    reminder_tone: Optional[str] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class WeeklySleepOut(BaseModel):
    day: str
    hours: float


class SleepStatsOut(BaseModel):
    week: list[WeeklySleepOut]
    avg_sleep_time: Optional[str] = None
    avg_wake_time: Optional[str] = None


class SleepOccurrenceOut(BaseModel):
    checkin_label_key: str
    time: str


class SleepFactorOut(BaseModel):
    name_key: str
    level: FactorLevel
    occurrences: list[SleepOccurrenceOut]

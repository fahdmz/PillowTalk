from typing import Literal, Optional

from pydantic import BaseModel, Field

Language = Literal["en", "id"]
FactorLevel = Literal["low", "medium", "high"]
TrendStatus = Literal["observed", "insufficient_data"]


class ProfileOut(BaseModel):
    id: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    language: Language = "id"
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
    avg_sleep_hours: Optional[float] = None
    sample_size: int = Field(default=0, ge=0)
    trend_status: TrendStatus = "insufficient_data"


class SleepOccurrenceOut(BaseModel):
    checkin_label_key: str
    time: str
    evidence_kind: Optional[Literal["user_reported", "system_inferred"]] = None
    source: Optional[Literal["local", "foundry_fallback", "rules"]] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)


class SleepFactorOut(BaseModel):
    name_key: str
    level: FactorLevel
    occurrences: list[SleepOccurrenceOut]
    trend_status: TrendStatus = "insufficient_data"
    sample_size: int = Field(default=0, ge=0)
    mean_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    interpretation: Literal["observed_alongside_checkins"] = (
        "observed_alongside_checkins"
    )

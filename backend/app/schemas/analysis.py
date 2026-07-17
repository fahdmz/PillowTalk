import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

_WAKE_TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class Emotion(StrEnum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    LOVE = "love"
    NEUTRAL = "neutral"


class Domain(StrEnum):
    RELATIONSHIP = "relationship"
    SLEEP = "sleep"
    WORK = "work"
    HEALTH = "health"
    SLEEP_SUBSTANCES = "sleep_substances"


class SleepSubstance(StrEnum):
    CAFFEINE = "caffeine"
    ALCOHOL = "alcohol"
    NICOTINE = "nicotine"
    SLEEP_MEDICATION = "sleep_medication"
    OTHER_STIMULANT = "other_stimulant"
    OTHER_SEDATIVE = "other_sedative"


class AnalysisSource(StrEnum):
    LOCAL = "local"
    FOUNDRY_FALLBACK = "foundry_fallback"
    RULES = "rules"


class RiskLevel(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExtractedContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domains: list[Domain] = Field(default_factory=list)
    sleep_substances: list[SleepSubstance] = Field(default_factory=list)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    wake_time: str | None = None

    @field_validator("wake_time")
    @classmethod
    def validate_wake_time(cls, value: str | None) -> str | None:
        if value is not None and not _WAKE_TIME_PATTERN.fullmatch(value):
            raise ValueError("wake_time must use 24-hour HH:MM format")
        return value


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    emotion: Emotion
    domains: list[Domain]
    sleep_substances: list[SleepSubstance]
    sleep_hours: float | None = Field(ge=0, le=24)
    wake_time: str | None
    confidence: float = Field(ge=0, le=1)
    source: AnalysisSource
    risk_level: RiskLevel
    emotion_scores: dict[str, float]
    model_id: str | None
    model_revision: str | None

    @field_validator("wake_time")
    @classmethod
    def validate_wake_time(cls, value: str | None) -> str | None:
        if value is not None and not _WAKE_TIME_PATTERN.fullmatch(value):
            raise ValueError("wake_time must use 24-hour HH:MM format")
        return value

    @field_validator("emotion_scores")
    @classmethod
    def validate_emotion_scores(cls, values: dict[str, float]) -> dict[str, float]:
        allowed = {emotion.value for emotion in Emotion}
        if any(label not in allowed for label in values):
            raise ValueError("emotion_scores contains an unsupported emotion")
        if any(score < 0 or score > 1 for score in values.values()):
            raise ValueError("emotion scores must be between 0 and 1")
        return values

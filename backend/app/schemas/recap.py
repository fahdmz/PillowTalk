from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from .analysis import Domain, Emotion
from .chat import ChatMessageOut


class RecapListItem(BaseModel):
    id: str
    session_id: Optional[str] = None
    date: str
    time: str
    is_night: bool
    preview: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    dominant_emotion: Optional[Emotion] = None
    domains: list[Domain] = Field(default_factory=list)


class RecapDetail(RecapListItem):
    conclusion: Optional[str] = None
    emotional_trend: dict[str, Any] = Field(default_factory=dict)
    sleep_observations: list[str] = Field(default_factory=list)
    generated_at: Optional[datetime] = None
    transcript: list[ChatMessageOut]

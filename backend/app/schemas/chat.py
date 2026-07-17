from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

CheckinMode = Literal["night", "morning"]
Language = Literal["en", "id"]
SessionStatus = Literal["active", "completed"]


class StartSessionRequest(BaseModel):
    checkin_mode: CheckinMode
    language: Language = "en"


class ChatMessageOut(BaseModel):
    id: str
    sender: Literal["ai", "user"]
    text: Optional[str] = None
    is_crisis: bool = False
    crisis_prefix: Optional[str] = None
    crisis_phone: Optional[str] = None
    crisis_suffix: Optional[str] = None
    created_at: Optional[datetime] = None


class StartSessionResponse(BaseModel):
    session_id: str
    checkin_mode: CheckinMode
    greeting: ChatMessageOut


class SendMessageRequest(BaseModel):
    session_id: str
    text: str
    language: Language = "en"


class SendMessageResponse(BaseModel):
    user_message: ChatMessageOut
    ai_message: ChatMessageOut
    session_status: SessionStatus

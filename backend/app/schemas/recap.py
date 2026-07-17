from typing import Optional

from pydantic import BaseModel

from .chat import ChatMessageOut


class RecapListItem(BaseModel):
    id: str
    date: str
    time: str
    is_night: bool
    preview: Optional[str] = None


class RecapDetail(BaseModel):
    id: str
    date: str
    time: str
    is_night: bool
    transcript: list[ChatMessageOut]

import asyncio

import pytest
from fastapi import HTTPException

from app.routers import chat
from app.services.recap_generator import RecapGenerationError


class FailingRecapService:
    async def generate_for_session(self, **kwargs):
        raise RecapGenerationError("temporary Foundry failure")


def test_recap_generation_failure_is_retryable_after_session_is_completed(monkeypatch):
    monkeypatch.setattr(chat, "_get_supabase", lambda: object())
    monkeypatch.setattr(
        chat,
        "_get_owned_session",
        lambda sb, session_id, user_id: {"id": session_id, "status": "completed"},
    )

    with pytest.raises(HTTPException) as raised:
        asyncio.run(
            chat.end_session_early(
                "session-1",
                user_id="user-1",
                recap_service=FailingRecapService(),
            )
        )

    assert raised.value.status_code == 503
    assert raised.value.headers == {"Retry-After": "2"}
    assert raised.value.detail == "Recap generation is temporarily unavailable"

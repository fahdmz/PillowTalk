import asyncio

import pytest
from fastapi import HTTPException

from app.routers.chat import send_message
from app.schemas.analysis import AnalysisResult, AnalysisSource, Emotion, RiskLevel
from app.schemas.chat import SendMessageRequest
from app.services.chat_orchestrator import (
    ChatTurnResult,
    SessionCompletedError,
    SessionNotFoundError,
)


def analysis():
    return AnalysisResult(
        emotion=Emotion.NEUTRAL,
        domains=[],
        sleep_substances=[],
        sleep_hours=None,
        wake_time=None,
        confidence=0.8,
        source=AnalysisSource.LOCAL,
        risk_level=RiskLevel.NONE,
        emotion_scores={"neutral": 0.8},
        model_id="local/model",
        model_revision="revision",
    )


class FakeOrchestrator:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    async def send_message(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return ChatTurnResult(
            user_message={"id": "user-message", "sender": "user", "text": kwargs["text"]},
            ai_message={"id": "ai-message", "sender": "ai", "text": "Halo kembali"},
            session_status="active",
            analysis=analysis(),
        )


def test_message_route_passes_verified_user_to_orchestrator():
    orchestrator = FakeOrchestrator()

    response = asyncio.run(
        send_message(
            SendMessageRequest(session_id="session-1", text="Halo", language="id"),
            user_id="user-1",
            orchestrator=orchestrator,
        )
    )

    assert orchestrator.calls[0]["user_id"] == "user-1"
    assert response.ai_message.text == "Halo kembali"


@pytest.mark.parametrize(
    ("error", "status_code"),
    [(SessionNotFoundError(), 404), (SessionCompletedError(), 400)],
)
def test_message_route_maps_domain_errors_to_http(error, status_code):
    with pytest.raises(HTTPException) as raised:
        asyncio.run(
            send_message(
                SendMessageRequest(session_id="session-1", text="Halo", language="id"),
                user_id="user-1",
                orchestrator=FakeOrchestrator(error=error),
            )
        )

    assert raised.value.status_code == status_code

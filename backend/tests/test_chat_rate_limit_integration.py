import asyncio

import pytest
from fastapi import HTTPException

from app.routers.chat import send_message
from app.schemas.chat import SendMessageRequest
from app.services.chat_orchestrator import ChatOrchestrator
from app.services.rate_limiter import RateLimitExceeded
from app.services.safety import SafetyScreen


class RejectingLimiter:
    def __init__(self):
        self.users = []

    def check(self, user_id):
        self.users.append(user_id)
        raise RateLimitExceeded(17)


class UntouchedRepository:
    def __init__(self):
        self.calls = 0

    def get_owned_session(self, session_id, user_id):
        self.calls += 1
        return None


class RaisingOrchestrator:
    async def send_message(self, **kwargs):
        raise RateLimitExceeded(17)


def test_orchestrator_rate_limits_before_database_or_model_work():
    repository = UntouchedRepository()
    limiter = RejectingLimiter()
    orchestrator = ChatOrchestrator(
        repository=repository,
        safety_screen=SafetyScreen(),
        analyzer=object(),
        chatbot=object(),
        rate_limiter=limiter,
        resource_name="Healing119",
        resource_phone="119 ext. 8",
        resource_url="https://www.healing119.id",
    )

    with pytest.raises(RateLimitExceeded):
        asyncio.run(
            orchestrator.send_message(
                user_id="user-1",
                session_id="session-1",
                text="Halo",
                language="id",
            )
        )

    assert limiter.users == ["user-1"]
    assert repository.calls == 0


def test_route_returns_429_and_retry_after_header():
    with pytest.raises(HTTPException) as raised:
        asyncio.run(
            send_message(
                SendMessageRequest(session_id="session-1", text="Halo", language="id"),
                user_id="user-1",
                orchestrator=RaisingOrchestrator(),
            )
        )

    assert raised.value.status_code == 429
    assert raised.value.headers == {"Retry-After": "17"}

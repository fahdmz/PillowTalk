import asyncio

from app.services.idempotent_orchestrator import IdempotentChatOrchestrator


class Repository:
    def get_owned_session(self, session_id, user_id):
        return {"id": session_id, "status": "active", "checkin_mode": "night"}
    def find_idempotent_turn(self, session_id, key):
        return {
            "user_message": {"id": "user-message", "sender": "user", "text": "Halo"},
            "ai_message": {"id": "ai-message", "sender": "ai", "text": "Hai"},
        }


class Inner:
    def __init__(self): self.repository = Repository(); self.calls = []
    async def send_message(self, **kwargs): self.calls.append(kwargs)


def test_completed_retry_replays_without_calling_inner_models():
    inner = Inner()
    orchestrator = IdempotentChatOrchestrator(inner)

    result = asyncio.run(orchestrator.send_message(
        user_id="user-1", session_id="session-1", text="Halo", language="id",
        idempotency_key="request-123",
    ))

    assert result.ai_message["id"] == "ai-message"
    assert inner.calls == []

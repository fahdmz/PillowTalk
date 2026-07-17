import asyncio
from types import SimpleNamespace

from app.routers import chat


class UpdateQuery:
    def __init__(self):
        self.payload = None
        self.filters = []

    def update(self, payload):
        self.payload = payload
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def execute(self):
        return SimpleNamespace(data=[])


class FakeSupabase:
    def __init__(self):
        self.query = UpdateQuery()

    def table(self, name):
        assert name == "chat_sessions"
        return self.query


class FakeRecapService:
    def __init__(self):
        self.calls = []

    async def generate_for_session(self, **kwargs):
        self.calls.append(kwargs)
        return {"id": "recap-1"}


def test_ending_session_marks_it_completed_then_generates_recap(monkeypatch):
    supabase = FakeSupabase()
    recap_service = FakeRecapService()
    monkeypatch.setattr(chat, "_get_supabase", lambda: supabase)
    monkeypatch.setattr(
        chat,
        "_get_owned_session",
        lambda sb, session_id, user_id: {"id": session_id, "status": "active"},
    )
    monkeypatch.setattr(chat, "_first_user_message_preview", lambda sb, sid: "Halo")

    asyncio.run(
        chat.end_session_early(
            "session-1",
            user_id="user-1",
            recap_service=recap_service,
        )
    )

    assert supabase.query.payload["status"] == "completed"
    assert supabase.query.payload["preview"] == "Halo"
    assert recap_service.calls == [
        {"user_id": "user-1", "session_id": "session-1"}
    ]

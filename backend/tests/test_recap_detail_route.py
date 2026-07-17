from types import SimpleNamespace

from app.routers.recaps import get_recap


class Query:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.filters = []

    def select(self, columns):
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def limit(self, value):
        return self

    def order(self, column, **kwargs):
        return self

    def execute(self):
        self.client.queries.append(self)
        return SimpleNamespace(data=self.client.responses[self.table].pop(0))


class FakeSupabase:
    def __init__(self, responses):
        self.responses = responses
        self.queries = []

    def table(self, name):
        return Query(self, name)


def test_recap_detail_checks_ownership_then_returns_exact_session_transcript(monkeypatch):
    sb = FakeSupabase(
        {
            "session_recaps": [[{
                "id": "recap-1",
                "session_id": "session-1",
                "title": "Pagi yang tenang",
                "summary": "Kamu merasa lebih tenang.",
                "conclusion": "Ketenangan menonjol pagi ini.",
                "dominant_emotion": "neutral",
                "domains": ["sleep"],
                "emotional_trend": {
                    "direction": "stabil",
                    "observation": "Nada percakapan stabil.",
                },
                "sleep_observations": ["Pengguna melaporkan tidur tujuh jam."],
                "generated_at": "2026-07-18T00:10:00+00:00",
                "chat_sessions": {
                    "id": "session-1",
                    "started_at": "2026-07-18T00:00:00+00:00",
                    "checkin_mode": "morning",
                    "preview": "Tidurku lumayan",
                },
            }]],
            "chat_messages": [[
                {"id": "message-1", "sender": "user", "text": "Tidurku lumayan"},
                {"id": "message-2", "sender": "ai", "text": "Senang mendengarnya."},
            ]],
        }
    )
    monkeypatch.setattr("app.routers.recaps.get_supabase", lambda: sb)

    detail = get_recap("recap-1", user_id="user-1")

    recap_query, message_query = sb.queries
    assert ("id", "recap-1") in recap_query.filters
    assert ("chat_sessions.user_id", "user-1") in recap_query.filters
    assert message_query.filters == [("session_id", "session-1")]
    assert detail.session_id == "session-1"
    assert detail.conclusion == "Ketenangan menonjol pagi ini."
    assert [message.text for message in detail.transcript] == [
        "Tidurku lumayan",
        "Senang mendengarnya.",
    ]

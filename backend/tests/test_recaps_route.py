from types import SimpleNamespace

from app.routers.recaps import list_recaps


class Query:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.filters = []

    def select(self, columns):
        return self

    def eq(self, column, value):
        self.filters.append(("eq", column, value))
        return self

    def gte(self, column, value):
        self.filters.append(("gte", column, value))
        return self

    def lt(self, column, value):
        self.filters.append(("lt", column, value))
        return self

    def order(self, column, **kwargs):
        return self

    def execute(self):
        self.client.queries.append(self)
        return SimpleNamespace(data=self.client.responses[self.table])


class FakeSupabase:
    def __init__(self, responses):
        self.responses = responses
        self.queries = []

    def table(self, name):
        return Query(self, name)


def test_list_recaps_reads_generated_recaps_and_preserves_ui_fields(monkeypatch):
    sb = FakeSupabase(
        {
            "session_recaps": [
                {
                    "id": "recap-1",
                    "title": "Malam yang berat",
                    "summary": "Kamu membahas tekanan kerja.",
                    "dominant_emotion": "sadness",
                    "domains": ["work"],
                    "chat_sessions": {
                        "id": "session-1",
                        "started_at": "2026-07-17T21:05:00+00:00",
                        "checkin_mode": "night",
                        "preview": "Aku capek",
                    },
                }
            ]
        }
    )
    monkeypatch.setattr("app.routers.recaps.get_supabase", lambda: sb)

    rows = list_recaps(filter="all", month=None, user_id="user-1")

    assert rows[0].id == "recap-1"
    assert rows[0].title == "Malam yang berat"
    assert rows[0].summary == "Kamu membahas tekanan kerja."
    assert rows[0].date == "2026-07-17"
    assert rows[0].is_night is True
    assert ("eq", "chat_sessions.user_id", "user-1") in sb.queries[0].filters
    assert ("eq", "chat_sessions.status", "completed") in sb.queries[0].filters

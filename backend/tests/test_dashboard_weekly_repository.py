from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.dashboard import SupabaseDashboardRepository


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

    def in_(self, column, values):
        self.filters.append(("in", column, values))
        return self

    def gte(self, column, value):
        self.filters.append(("gte", column, value))
        return self

    def order(self, column, **kwargs):
        return self

    def execute(self):
        self.client.queries.append(self)
        return SimpleNamespace(data=self.client.responses[self.table].pop(0))


class FakeSupabase:
    def __init__(self):
        self.responses = {
            "chat_sessions": [[{"id": "session-1"}]],
            "message_analyses": [[{
                "session_id": "session-1",
                "sleep_hours": 7.5,
                "wake_time": "06:30",
                "created_at": "2026-07-17T01:00:00+00:00",
            }]],
        }
        self.queries = []

    def table(self, name):
        return Query(self, name)


def test_weekly_sleep_repository_scopes_analyses_through_owned_sessions():
    sb = FakeSupabase()
    since = datetime(2026, 7, 11, 17, 0, tzinfo=timezone.utc)

    rows = SupabaseDashboardRepository(sb).load_sleep_analyses(
        user_id="user-1",
        since=since,
    )

    session_query, analysis_query = sb.queries
    assert ("eq", "user_id", "user-1") in session_query.filters
    assert ("in", "session_id", ["session-1"]) in analysis_query.filters
    assert ("gte", "created_at", since.isoformat()) in analysis_query.filters
    assert rows[0]["sleep_hours"] == 7.5

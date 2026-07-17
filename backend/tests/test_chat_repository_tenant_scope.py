from types import SimpleNamespace

from app.services.chat_repository import SupabaseChatRepository


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

    def in_(self, column, values):
        self.filters.append(("in", column, values))
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, value):
        return self

    def execute(self):
        self.client.calls.append(self)
        if self.table == "chat_sessions":
            return SimpleNamespace(data=[{"id": "session-1"}, {"id": "session-2"}])
        return SimpleNamespace(data=[])


class FakeSupabase:
    def __init__(self):
        self.calls = []

    def table(self, name):
        return Query(self, name)


def test_historical_analysis_uses_owned_session_ids_with_service_role_client():
    sb = FakeSupabase()
    repository = SupabaseChatRepository(sb)

    repository.load_chat_context("user-1", "session-1")

    owned_sessions = next(call for call in sb.calls if call.table == "chat_sessions")
    analysis_query = next(call for call in sb.calls if call.table == "message_analyses")
    assert ("eq", "user_id", "user-1") in owned_sessions.filters
    assert ("in", "session_id", ["session-1", "session-2"]) in analysis_query.filters

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
            "sleep_factors": [[
                {"id": "factor-work", "name_key": "work"},
                {"id": "factor-caffeine", "name_key": "caffeine"},
            ]],
            "sleep_factor_occurrences": [[
                {
                    "factor_id": "factor-work",
                    "occurred_at": "2026-07-17T01:00:00+00:00",
                }
            ]],
        }
        self.queries = []

    def table(self, name):
        return Query(self, name)


def test_factor_repository_uses_two_bounded_owned_queries():
    sb = FakeSupabase()
    since = datetime(2026, 6, 18, tzinfo=timezone.utc)

    rows = SupabaseDashboardRepository(sb).load_sleep_factors(
        user_id="user-1",
        since=since,
    )

    factor_query, occurrence_query = sb.queries
    assert ("eq", "user_id", "user-1") in factor_query.filters
    assert ("in", "factor_id", ["factor-work", "factor-caffeine"]) in occurrence_query.filters
    assert ("gte", "occurred_at", since.isoformat()) in occurrence_query.filters
    assert rows[0]["name_key"] == "work"
    assert rows[0]["sample_size"] == 1

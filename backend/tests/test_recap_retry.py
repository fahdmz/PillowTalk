import asyncio
from types import SimpleNamespace

from app.services.recap_repository import SupabaseRecapRepository
from app.services.recap_service import RecapService


class SelectQuery:
    def __init__(self, row):
        self.row = row
        self.filters = []

    def select(self, columns):
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def limit(self, value):
        return self

    def execute(self):
        return SimpleNamespace(data=[self.row])


class SelectClient:
    def __init__(self, row):
        self.query = SelectQuery(row)

    def table(self, name):
        assert name == "session_recaps"
        return self.query


def test_existing_recap_lookup_is_scoped_to_session():
    client = SelectClient({"id": "recap-1"})

    row = SupabaseRecapRepository(client).find_recap("session-1")

    assert row == {"id": "recap-1"}
    assert client.query.filters == [("session_id", "session-1")]


class ExistingRepository:
    def __init__(self):
        self.loaded_inputs = False

    def get_owned_completed_session(self, session_id, user_id):
        return {"id": session_id, "checkin_mode": "morning"}

    def find_recap(self, session_id):
        return {"id": "recap-1", "session_id": session_id}

    def load_messages(self, session_id):
        self.loaded_inputs = True
        return []


class UnusedGenerator:
    deployment = "gpt-recap"

    async def generate(self, **kwargs):
        raise AssertionError("Foundry must not be called for an existing recap")


def test_retry_returns_existing_recap_without_loading_inputs_or_calling_foundry():
    repository = ExistingRepository()

    row = asyncio.run(
        RecapService(repository=repository, generator=UnusedGenerator())
        .generate_for_session(user_id="user-1", session_id="session-1")
    )

    assert row["id"] == "recap-1"
    assert repository.loaded_inputs is False

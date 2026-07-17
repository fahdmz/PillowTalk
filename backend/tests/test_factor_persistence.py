from types import SimpleNamespace

from app.schemas.analysis import (
    AnalysisResult,
    AnalysisSource,
    Domain,
    Emotion,
    RiskLevel,
    SleepSubstance,
)
from app.services.chat_repository import SupabaseChatRepository


class Query:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.operation = None
        self.payload = None
        self.filters = []

    def select(self, columns, **kwargs):
        self.operation = "select"
        return self

    def upsert(self, payload, **kwargs):
        self.operation = "upsert"
        self.payload = payload
        self.upsert_options = kwargs
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def execute(self):
        self.client.calls.append(self)
        if self.table == "sleep_factors" and self.operation == "upsert":
            return SimpleNamespace(data=[{"id": f"factor-{self.payload['name_key']}"}])
        return SimpleNamespace(data=[])


class FakeSupabase:
    def __init__(self):
        self.calls = []

    def table(self, name):
        return Query(self, name)


def test_canonical_domains_and_substances_are_linked_to_source_message():
    sb = FakeSupabase()
    repository = SupabaseChatRepository(sb)
    result = AnalysisResult(
        emotion=Emotion.SADNESS,
        domains=[Domain.WORK, Domain.SLEEP_SUBSTANCES],
        sleep_substances=[SleepSubstance.CAFFEINE, SleepSubstance.ALCOHOL],
        sleep_hours=None,
        wake_time=None,
        confidence=0.84,
        source=AnalysisSource.LOCAL,
        risk_level=RiskLevel.NONE,
        emotion_scores={"sadness": 0.84},
        model_id="local/model",
        model_revision="revision",
    )

    repository.save_factor_occurrences(
        user_id="user-1",
        session_id="session-1",
        message_id="message-1",
        checkin_mode="night",
        analysis=result,
    )

    factor_upserts = [call for call in sb.calls if call.table == "sleep_factors"]
    assert [call.payload["name_key"] for call in factor_upserts] == [
        "work",
        "caffeine",
        "alcohol",
    ]
    occurrences = [
        call.payload for call in sb.calls if call.table == "sleep_factor_occurrences"
    ]
    assert all(row["message_id"] == "message-1" for row in occurrences)
    assert all(row["evidence_kind"] == "user_reported" for row in occurrences)
    assert all(row["source"] == "local" for row in occurrences)
    assert all(row["confidence"] == 0.84 for row in occurrences)

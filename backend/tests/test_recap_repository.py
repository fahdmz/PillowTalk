from types import SimpleNamespace

from app.services.recap_generator import EmotionalTrend, RecapOutput
from app.services.recap_repository import SupabaseRecapRepository


class Query:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.operation = None
        self.payload = None
        self.filters = []
        self.limit_value = None
        self.columns = None
        self.on_conflict = None

    def select(self, columns):
        self.operation = "select"
        self.columns = columns
        return self

    def upsert(self, payload, *, on_conflict):
        self.operation = "upsert"
        self.payload = payload
        self.on_conflict = on_conflict
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def order(self, column, **kwargs):
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def execute(self):
        self.client.calls.append(self)
        queue = self.client.responses.get((self.table, self.operation), [])
        data = queue.pop(0) if queue else []
        return SimpleNamespace(data=data)


class FakeSupabase:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def table(self, name):
        return Query(self, name)


def test_completed_session_lookup_is_scoped_by_session_user_and_status():
    sb = FakeSupabase({("chat_sessions", "select"): [[{"id": "session-1"}]]})

    row = SupabaseRecapRepository(sb).get_owned_completed_session(
        "session-1", "user-1"
    )

    assert row == {"id": "session-1"}
    assert sb.calls[0].filters == [
        ("id", "session-1"),
        ("user_id", "user-1"),
        ("status", "completed"),
    ]


def test_generation_inputs_are_session_scoped_bounded_and_exclude_unneeded_columns():
    sb = FakeSupabase(
        {
            ("chat_messages", "select"): [[{"sender": "user", "text": "Halo"}]],
            ("message_analyses", "select"): [[{"emotion": "neutral"}]],
        }
    )
    repository = SupabaseRecapRepository(sb, generation_input_limit=200)

    messages = repository.load_messages("session-1")
    analyses = repository.load_analyses("session-1")

    message_query, analysis_query = sb.calls
    assert messages == [{"sender": "user", "text": "Halo"}]
    assert analyses == [{"emotion": "neutral"}]
    assert message_query.filters == [("session_id", "session-1")]
    assert message_query.limit_value == 200
    assert message_query.columns == "sender,text,created_at"
    assert analysis_query.filters == [("session_id", "session-1")]
    assert analysis_query.limit_value == 200
    assert "emotion_scores" not in analysis_query.columns


def test_recap_is_upserted_by_session_with_model_metadata():
    sb = FakeSupabase(
        {("session_recaps", "upsert"): [[{"id": "recap-1", "session_id": "session-1"}]]}
    )
    recap = RecapOutput(
        title="Malam yang berat",
        summary="Kamu merasa lelah.",
        conclusion="Rasa lelah menonjol malam ini.",
        dominant_emotion="sadness",
        domains=["work"],
        emotional_trend=EmotionalTrend(
            direction="tidak_cukup_data",
            observation="Hanya ada satu laporan.",
        ),
        sleep_observations=[],
    )

    row = SupabaseRecapRepository(sb).save_recap(
        "session-1",
        recap,
        model_deployment="gpt-recap",
        prompt_version="recap-id-v1",
    )

    query = sb.calls[0]
    assert row["id"] == "recap-1"
    assert query.on_conflict == "session_id"
    assert query.payload["dominant_emotion"] == "sadness"
    assert query.payload["emotional_trend"]["direction"] == "tidak_cukup_data"
    assert query.payload["model_deployment"] == "gpt-recap"
    assert query.payload["prompt_version"] == "recap-id-v1"

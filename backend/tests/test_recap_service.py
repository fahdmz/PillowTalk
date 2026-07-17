import asyncio

from app.services.recap_generator import EmotionalTrend, RecapOutput
from app.services.recap_service import RecapService


class FakeRepository:
    def __init__(self):
        self.saved = []

    def get_owned_completed_session(self, session_id, user_id):
        return {"id": session_id, "checkin_mode": "night", "status": "completed"}

    def find_recap(self, session_id):
        return None

    def load_messages(self, session_id):
        return [{"sender": "user", "text": "Aku capek."}]

    def load_analyses(self, session_id):
        return [{"emotion": "sadness", "domains": ["work"]}]

    def save_recap(self, session_id, recap, *, model_deployment, prompt_version):
        row = {"id": "recap-1", "session_id": session_id, **recap.model_dump(mode="json")}
        self.saved.append(
            {
                "row": row,
                "model_deployment": model_deployment,
                "prompt_version": prompt_version,
            }
        )
        return row


class FakeGenerator:
    deployment = "gpt-recap"

    def __init__(self):
        self.calls = []

    async def generate(self, **kwargs):
        self.calls.append(kwargs)
        return RecapOutput(
            title="Malam yang berat",
            summary="Kamu bercerita tentang rasa lelah.",
            conclusion="Rasa lelah menonjol malam ini.",
            dominant_emotion="sadness",
            domains=["work"],
            emotional_trend=EmotionalTrend(
                direction="tidak_cukup_data",
                observation="Hanya ada satu laporan emosi.",
            ),
            sleep_observations=[],
        )


def test_completed_owned_session_generates_and_persists_one_recap():
    repository = FakeRepository()
    generator = FakeGenerator()

    row = asyncio.run(
        RecapService(repository=repository, generator=generator).generate_for_session(
            user_id="user-1",
            session_id="session-1",
        )
    )

    assert row["id"] == "recap-1"
    assert generator.calls == [
        {
            "checkin_mode": "night",
            "messages": [{"sender": "user", "text": "Aku capek."}],
            "analyses": [{"emotion": "sadness", "domains": ["work"]}],
        }
    ]
    assert repository.saved[0]["model_deployment"] == "gpt-recap"
    assert repository.saved[0]["prompt_version"] == "recap-id-v1"

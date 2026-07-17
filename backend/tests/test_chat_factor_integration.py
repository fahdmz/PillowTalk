import asyncio

from app.schemas.analysis import (
    AnalysisResult,
    AnalysisSource,
    Domain,
    Emotion,
    RiskLevel,
)
from app.services.chat_orchestrator import ChatOrchestrator
from app.services.safety import SafetyScreen


class Repository:
    def __init__(self):
        self.messages = []
        self.factor_calls = []

    def get_owned_session(self, session_id, user_id):
        return {"id": session_id, "status": "active", "checkin_mode": "night"}

    def insert_message(self, session_id, sender, text, *, is_crisis=False):
        row = {"id": f"message-{len(self.messages) + 1}", "sender": sender, "text": text}
        self.messages.append(row)
        return row

    def save_analysis(self, message_id, session_id, analysis): pass
    def load_chat_context(self, user_id, session_id): return {}
    def save_factor_occurrences(self, **kwargs): self.factor_calls.append(kwargs)


class Analyzer:
    async def analyze(self, text):
        return AnalysisResult(
            emotion=Emotion.SADNESS,
            domains=[Domain.WORK],
            sleep_substances=[],
            sleep_hours=None,
            wake_time=None,
            confidence=0.8,
            source=AnalysisSource.LOCAL,
            risk_level=RiskLevel.NONE,
            emotion_scores={"sadness": 0.8},
            model_id="local/model",
            model_revision="revision",
        )


class Chatbot:
    async def respond(self, **kwargs): return "Aku mendengarkan"


def test_normal_chat_turn_persists_factors_for_exact_user_message():
    repository = Repository()
    orchestrator = ChatOrchestrator(
        repository=repository,
        safety_screen=SafetyScreen(),
        analyzer=Analyzer(),
        chatbot=Chatbot(),
        resource_name="Healing119",
        resource_phone="119 ext. 8",
        resource_url="https://www.healing119.id",
    )

    asyncio.run(
        orchestrator.send_message(
            user_id="user-1",
            session_id="session-1",
            text="Kerjaan membuatku kepikiran",
            language="id",
        )
    )

    assert repository.factor_calls[0]["user_id"] == "user-1"
    assert repository.factor_calls[0]["message_id"] == "message-1"
    assert repository.factor_calls[0]["checkin_mode"] == "night"

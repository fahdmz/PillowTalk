import asyncio

from app.schemas.analysis import AnalysisResult, AnalysisSource, Emotion, RiskLevel
from app.services.chat_orchestrator import ChatOrchestrator, SessionCompletedError
from app.services.safety import SafetyScreen


def normal_analysis() -> AnalysisResult:
    return AnalysisResult(
        emotion=Emotion.SADNESS,
        domains=[],
        sleep_substances=[],
        sleep_hours=None,
        wake_time=None,
        confidence=0.82,
        source=AnalysisSource.LOCAL,
        risk_level=RiskLevel.NONE,
        emotion_scores={"sadness": 0.82},
        model_id="local/model",
        model_revision="revision",
    )


class FakeAnalyzer:
    def __init__(self):
        self.calls = []

    async def analyze(self, text):
        self.calls.append(text)
        return normal_analysis()


class FakeChatbot:
    def __init__(self, reply="Aku mendengarkan. Mau cerita lebih jauh?", error=None):
        self.reply = reply
        self.error = error
        self.calls = []

    async def respond(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.reply


class FakeRepository:
    def __init__(self, *, status="active"):
        self.session = {
            "id": "session-1",
            "user_id": "user-1",
            "status": status,
            "checkin_mode": "night",
        }
        self.messages = []
        self.analyses = []
        self.safety_events = []
        self.crisis_sessions = []

    def get_owned_session(self, session_id, user_id):
        return self.session if (session_id, user_id) == ("session-1", "user-1") else None

    def insert_message(self, session_id, sender, text, *, is_crisis=False):
        row = {
            "id": f"message-{len(self.messages) + 1}",
            "session_id": session_id,
            "sender": sender,
            "text": text,
            "is_crisis": is_crisis,
        }
        self.messages.append(row)
        return row

    def save_analysis(self, message_id, session_id, analysis):
        self.analyses.append((message_id, session_id, analysis))

    def save_safety_event(self, message_id, session_id, result):
        self.safety_events.append((message_id, session_id, result))

    def mark_session_crisis(self, session_id):
        self.crisis_sessions.append(session_id)

    def load_chat_context(self, user_id, session_id):
        return {
            "recent_messages": [{"sender": "user", "text": "Pesan sebelumnya"}],
            "recent_recaps": [],
            "emotional_trends": [],
        }


def build_orchestrator(repository, analyzer, chatbot):
    return ChatOrchestrator(
        repository=repository,
        safety_screen=SafetyScreen(),
        analyzer=analyzer,
        chatbot=chatbot,
        resource_name="Healing119",
        resource_phone="119 ext. 8",
        resource_url="https://www.healing119.id",
    )


def test_critical_message_bypasses_all_models_and_persists_minimal_safety_metadata():
    repository = FakeRepository()
    analyzer = FakeAnalyzer()
    chatbot = FakeChatbot()

    result = asyncio.run(
        build_orchestrator(repository, analyzer, chatbot).send_message(
            user_id="user-1",
            session_id="session-1",
            text="Aku mau bunuh diri malam ini",
            language="id",
        )
    )

    assert analyzer.calls == []
    assert chatbot.calls == []
    assert result.ai_message["is_crisis"] is True
    assert repository.safety_events[0][2].risk_level is RiskLevel.CRITICAL
    assert repository.analyses[0][2].source is AnalysisSource.RULES
    assert repository.crisis_sessions == ["session-1"]


def test_normal_message_is_analyzed_before_bounded_context_reaches_chatbot():
    repository = FakeRepository()
    analyzer = FakeAnalyzer()
    chatbot = FakeChatbot()

    result = asyncio.run(
        build_orchestrator(repository, analyzer, chatbot).send_message(
            user_id="user-1",
            session_id="session-1",
            text="Aku sedih karena kerjaan hari ini",
            language="id",
        )
    )

    assert analyzer.calls == ["Aku sedih karena kerjaan hari ini"]
    assert repository.analyses[0][2].emotion is Emotion.SADNESS
    assert chatbot.calls[0]["analysis"].emotion is Emotion.SADNESS
    assert chatbot.calls[0]["context"]["recent_messages"]
    assert result.ai_message["text"].startswith("Aku mendengarkan")


def test_chatbot_timeout_returns_calm_indonesian_reply_and_keeps_user_message():
    repository = FakeRepository()
    analyzer = FakeAnalyzer()
    chatbot = FakeChatbot(error=TimeoutError("upstream timeout"))

    result = asyncio.run(
        build_orchestrator(repository, analyzer, chatbot).send_message(
            user_id="user-1",
            session_id="session-1",
            text="Hari ini cukup berat",
            language="id",
        )
    )

    assert "coba lagi" in result.ai_message["text"].casefold()
    assert repository.messages[0]["sender"] == "user"
    assert repository.messages[1]["sender"] == "ai"


def test_completed_session_is_rejected_before_message_insert():
    repository = FakeRepository(status="completed")

    with __import__("pytest").raises(SessionCompletedError):
        asyncio.run(
            build_orchestrator(repository, FakeAnalyzer(), FakeChatbot()).send_message(
                user_id="user-1",
                session_id="session-1",
                text="Halo",
                language="id",
            )
        )

    assert repository.messages == []

"""Durable idempotency wrapper around the protected chat orchestrator."""

from typing import Any

from app.schemas.analysis import AnalysisResult, AnalysisSource, Emotion, RiskLevel
from app.services.chat_orchestrator import ChatOrchestrator, ChatTurnResult, SessionCompletedError, SessionNotFoundError
from app.services.idempotency import IdempotencyPending


class IdempotentChatOrchestrator:
    def __init__(self, inner: ChatOrchestrator) -> None:
        self.inner = inner
        self.repository = inner.repository

    async def send_message(self, *, idempotency_key: str | None = None, **kwargs: Any) -> ChatTurnResult:
        if not idempotency_key:
            return await self.inner.send_message(**kwargs)
        if not 8 <= len(idempotency_key) <= 128:
            raise ValueError("Idempotency-Key must contain 8 to 128 characters")

        session_id = kwargs["session_id"]
        user_id = kwargs["user_id"]
        session = self.repository.get_owned_session(session_id, user_id)
        if session is None:
            raise SessionNotFoundError("Session not found")
        if session["status"] == "completed":
            raise SessionCompletedError("This check-in has already ended")

        existing = self.repository.find_idempotent_turn(session_id, idempotency_key)
        if existing is not None:
            if existing["ai_message"] is None:
                raise IdempotencyPending()
            return ChatTurnResult(
                user_message=existing["user_message"], ai_message=existing["ai_message"],
                session_status=session["status"], analysis=_replay_analysis(),
            )

        if self.inner.rate_limiter is not None:
            self.inner.rate_limiter.check(user_id)
        reserved = self.repository.reserve_idempotency_key(
            session_id, idempotency_key, text=kwargs["text"]
        )
        proxy = _ReservedTurnRepository(self.repository, reserved)
        execution = ChatOrchestrator(
            repository=proxy,
            safety_screen=self.inner.safety_screen,
            analyzer=self.inner.analyzer,
            chatbot=self.inner.chatbot,
            resource_name=self.inner.resource_name,
            resource_phone=self.inner.resource_phone,
            resource_url=self.inner.resource_url,
            rate_limiter=None,
            recap_service=self.inner.recap_service,
            max_user_turns=self.inner.max_user_turns,
        )
        return await execution.send_message(**kwargs)


class _ReservedTurnRepository:
    def __init__(self, repository: Any, user_message: dict[str, Any]) -> None:
        self._repository = repository
        self._user_message = user_message

    def __getattr__(self, name: str) -> Any:
        return getattr(self._repository, name)

    def insert_message(self, session_id: str, sender: str, text: str, *, is_crisis: bool = False) -> dict:
        if sender == "user":
            return self._user_message
        return self._repository.insert_reply(
            session_id, self._user_message["id"], text, is_crisis=is_crisis
        )


def _replay_analysis() -> AnalysisResult:
    return AnalysisResult(
        emotion=Emotion.NEUTRAL, domains=[], sleep_substances=[], sleep_hours=None,
        wake_time=None, confidence=0, source=AnalysisSource.RULES,
        risk_level=RiskLevel.NONE, emotion_scores={}, model_id=None, model_revision=None,
    )

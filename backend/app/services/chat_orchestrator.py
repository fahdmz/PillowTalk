"""Safe, local-first orchestration for one authenticated chat turn."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.schemas.analysis import AnalysisResult, AnalysisSource, Emotion, RiskLevel
from app.services.safety import SafetyScreen, build_safety_message

logger = logging.getLogger(__name__)


class SessionNotFoundError(LookupError):
    pass


class SessionCompletedError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChatTurnResult:
    user_message: dict[str, Any]
    ai_message: dict[str, Any]
    session_status: str
    analysis: AnalysisResult


class ChatOrchestrator:
    def __init__(
        self,
        *,
        repository: Any,
        safety_screen: SafetyScreen,
        analyzer: Any,
        chatbot: Any,
        resource_name: str,
        resource_phone: str,
        resource_url: str,
        rate_limiter: Any | None = None,
    ) -> None:
        self.repository = repository
        self.safety_screen = safety_screen
        self.analyzer = analyzer
        self.chatbot = chatbot
        self.resource_name = resource_name
        self.resource_phone = resource_phone
        self.resource_url = resource_url
        self.rate_limiter = rate_limiter

    async def send_message(
        self,
        *,
        user_id: str,
        session_id: str,
        text: str,
        language: str,
    ) -> ChatTurnResult:
        if self.rate_limiter is not None:
            self.rate_limiter.check(user_id)
        session = self.repository.get_owned_session(session_id, user_id)
        if session is None:
            raise SessionNotFoundError("Session not found")
        if session["status"] == "completed":
            raise SessionCompletedError("This check-in has already ended")

        user_message = self.repository.insert_message(session_id, "user", text)
        safety = self.safety_screen.screen(text)
        if safety.should_interrupt:
            analysis = _safety_analysis(safety.risk_level)
            self.repository.save_analysis(user_message["id"], session_id, analysis)
            self.repository.save_safety_event(user_message["id"], session_id, safety)
            self.repository.mark_session_crisis(session_id)
            safety_message = build_safety_message(
                language="id" if language == "id" else "en",
                resource_name=self.resource_name,
                resource_phone=self.resource_phone,
                resource_url=self.resource_url,
            )
            ai_message = self.repository.insert_message(
                session_id, "ai", safety_message.text, is_crisis=True
            )
            return ChatTurnResult(
                user_message=user_message,
                ai_message=ai_message,
                session_status=session["status"],
                analysis=analysis,
            )

        analysis = await self.analyzer.analyze(text)
        if safety.risk_level is not RiskLevel.NONE:
            analysis = analysis.model_copy(update={"risk_level": safety.risk_level})
        self.repository.save_analysis(user_message["id"], session_id, analysis)
        save_factors = getattr(self.repository, "save_factor_occurrences", None)
        if callable(save_factors):
            save_factors(
                user_id=user_id,
                session_id=session_id,
                message_id=user_message["id"],
                checkin_mode=session["checkin_mode"],
                analysis=analysis,
            )
        context = self.repository.load_chat_context(user_id, session_id)

        try:
            reply = await self.chatbot.respond(
                language=language,
                checkin_mode=session["checkin_mode"],
                user_message=text,
                analysis=analysis,
                context=context,
            )
        except Exception:
            logger.exception("Chat model unavailable; returning controlled reply")
            reply = _upstream_failure_reply(language)

        ai_message = self.repository.insert_message(session_id, "ai", reply)
        return ChatTurnResult(
            user_message=user_message,
            ai_message=ai_message,
            session_status=session["status"],
            analysis=analysis,
        )


def _safety_analysis(risk_level: RiskLevel) -> AnalysisResult:
    return AnalysisResult(
        emotion=Emotion.NEUTRAL,
        domains=[],
        sleep_substances=[],
        sleep_hours=None,
        wake_time=None,
        confidence=1,
        source=AnalysisSource.RULES,
        risk_level=risk_level,
        emotion_scores={"neutral": 1},
        model_id=None,
        model_revision=None,
    )


def _upstream_failure_reply(language: str) -> str:
    if language == "id":
        return (
            "Maaf, aku sedang kesulitan merespons. Pesanmu sudah tersimpan; "
            "silakan coba lagi sebentar lagi."
        )
    return (
        "Sorry, I'm having trouble responding. Your message was saved; "
        "please try again in a moment."
    )

"""User-scoped Supabase persistence for chat orchestration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from app.schemas.analysis import AnalysisResult, Domain
from app.services.context_builder import build_chat_context
from app.services.safety import SafetyResult


class SupabaseChatRepository:
    def __init__(
        self,
        supabase: Any,
        *,
        message_limit: int = 12,
        recap_limit: int = 3,
        lookback_days: int = 14,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        self.supabase = supabase
        self.message_limit = message_limit
        self.recap_limit = recap_limit
        self.lookback_days = lookback_days
        self.now_factory = now_factory or (lambda: datetime.now(timezone.utc))

    def get_owned_session(self, session_id: str, user_id: str) -> dict | None:
        rows = (
            self.supabase.table("chat_sessions")
            .select("*")
            .eq("id", session_id)
            .eq("user_id", user_id)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None

    def insert_message(
        self,
        session_id: str,
        sender: str,
        text: str,
        *,
        is_crisis: bool = False,
    ) -> dict:
        rows = (
            self.supabase.table("chat_messages")
            .insert(
                {
                    "session_id": session_id,
                    "sender": sender,
                    "text": text,
                    "is_crisis": is_crisis,
                }
            )
            .execute()
            .data
            or []
        )
        if not rows:
            raise RuntimeError("Supabase did not return the inserted chat message")
        return rows[0]

    def save_analysis(
        self,
        message_id: str,
        session_id: str,
        analysis: AnalysisResult,
    ) -> None:
        payload = analysis.model_dump(mode="json")
        payload.update({"message_id": message_id, "session_id": session_id})
        self.supabase.table("message_analyses").insert(payload).execute()

    def save_factor_occurrences(
        self,
        *,
        user_id: str,
        session_id: str,
        message_id: str,
        checkin_mode: str,
        analysis: AnalysisResult,
    ) -> None:
        factor_keys = [
            domain.value
            for domain in analysis.domains
            if domain is not Domain.SLEEP_SUBSTANCES
        ]
        factor_keys.extend(substance.value for substance in analysis.sleep_substances)
        checkin_label = (
            "Morning Check-in" if checkin_mode == "morning" else "Nightly Check-in"
        )
        for factor_key in dict.fromkeys(factor_keys):
            rows = (
                self.supabase.table("sleep_factors")
                .upsert(
                    {"user_id": user_id, "name_key": factor_key},
                    on_conflict="user_id,name_key",
                )
                .execute()
                .data
                or []
            )
            if not rows:
                raise RuntimeError("Supabase did not return the persisted sleep factor")
            self.supabase.table("sleep_factor_occurrences").insert(
                {
                    "factor_id": rows[0]["id"],
                    "session_id": session_id,
                    "message_id": message_id,
                    "checkin_label_key": checkin_label,
                    "evidence_kind": "user_reported",
                    "source": analysis.source.value,
                    "confidence": analysis.confidence,
                }
            ).execute()

    def save_safety_event(
        self,
        message_id: str,
        session_id: str,
        result: SafetyResult,
    ) -> None:
        self.supabase.table("safety_events").insert(
            {
                "message_id": message_id,
                "session_id": session_id,
                "risk_level": result.risk_level.value,
                "signal_codes": list(result.signal_codes),
                "source": "rules",
                "action_taken": "crisis_guidance_returned",
            }
        ).execute()

    def mark_session_crisis(self, session_id: str) -> None:
        self.supabase.table("chat_sessions").update({"is_crisis": True}).eq(
            "id", session_id
        ).execute()

    def count_user_messages(self, session_id: str) -> int:
        res = (
            self.supabase.table("chat_messages")
            .select("id", count="exact")
            .eq("session_id", session_id)
            .eq("sender", "user")
            .execute()
        )
        return res.count or 0

    def mark_session_completed(self, session_id: str) -> None:
        """Ends a check-in from within the conversation itself (AI-signaled
        close or the turn cap) — same finalization shape as the day-rollover
        path in routers/chat.py, just triggered mid-conversation."""
        rows = (
            self.supabase.table("chat_messages")
            .select("text")
            .eq("session_id", session_id)
            .eq("sender", "user")
            .order("created_at")
            .limit(1)
            .execute()
            .data
            or []
        )
        text = rows[0].get("text", "") if rows else ""
        preview = text if len(text) <= 60 else f"{text[:57]}…"
        self.supabase.table("chat_sessions").update(
            {
                "status": "completed",
                "ended_at": datetime.now(timezone.utc).isoformat(),
                "preview": preview,
            }
        ).eq("id", session_id).execute()

    def load_chat_context(self, user_id: str, session_id: str) -> dict[str, Any]:
        newest_messages = (
            self.supabase.table("chat_messages")
            .select("sender,text,is_crisis,created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(self.message_limit)
            .execute()
            .data
            or []
        )
        recaps = (
            self.supabase.table("session_recaps")
            .select(
                "title,summary,dominant_emotion,domains,generated_at,"
                "chat_sessions!inner(user_id,status)"
            )
            .eq("chat_sessions.user_id", user_id)
            .eq("chat_sessions.status", "completed")
            .order("generated_at", desc=True)
            .limit(self.recap_limit)
            .execute()
            .data
            or []
        )
        owned_sessions = (
            self.supabase.table("chat_sessions")
            .select("id")
            .eq("user_id", user_id)
            .execute()
            .data
            or []
        )
        session_ids = [row["id"] for row in owned_sessions]
        analyses: list[dict[str, Any]] = []
        if session_ids:
            since = self.now_factory() - timedelta(days=self.lookback_days)
            analyses = (
                self.supabase.table("message_analyses")
                .select(
                    "emotion,domains,sleep_substances,sleep_hours,wake_time,created_at"
                )
                .in_("session_id", session_ids)
                .gte("created_at", since.isoformat())
                .execute()
                .data
                or []
            )
        return build_chat_context(
            messages=list(reversed(newest_messages)),
            recaps=recaps,
            analyses=analyses,
            message_limit=self.message_limit,
            recap_limit=self.recap_limit,
        )

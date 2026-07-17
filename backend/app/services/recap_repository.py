"""User-scoped Supabase persistence for completed-session recaps."""

from __future__ import annotations

from typing import Any

from app.services.recap_generator import RecapOutput


class SupabaseRecapRepository:
    def __init__(self, supabase: Any, *, generation_input_limit: int = 200) -> None:
        self.supabase = supabase
        self.generation_input_limit = generation_input_limit

    def get_owned_completed_session(
        self,
        session_id: str,
        user_id: str,
    ) -> dict[str, Any] | None:
        rows = (
            self.supabase.table("chat_sessions")
            .select("*")
            .eq("id", session_id)
            .eq("user_id", user_id)
            .eq("status", "completed")
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None

    def find_recap(self, session_id: str) -> dict[str, Any] | None:
        rows = (
            self.supabase.table("session_recaps")
            .select("*")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None

    def load_messages(self, session_id: str) -> list[dict[str, Any]]:
        return (
            self.supabase.table("chat_messages")
            .select("sender,text,created_at")
            .eq("session_id", session_id)
            .order("created_at")
            .limit(self.generation_input_limit)
            .execute()
            .data
            or []
        )

    def load_analyses(self, session_id: str) -> list[dict[str, Any]]:
        return (
            self.supabase.table("message_analyses")
            .select(
                "emotion,domains,sleep_substances,sleep_hours,wake_time,"
                "confidence,source,risk_level,created_at"
            )
            .eq("session_id", session_id)
            .order("created_at")
            .limit(self.generation_input_limit)
            .execute()
            .data
            or []
        )

    def save_recap(
        self,
        session_id: str,
        recap: RecapOutput,
        *,
        model_deployment: str,
        prompt_version: str,
    ) -> dict[str, Any]:
        payload = recap.model_dump(mode="json")
        payload.update(
            {
                "session_id": session_id,
                "model_deployment": model_deployment,
                "prompt_version": prompt_version,
            }
        )
        rows = (
            self.supabase.table("session_recaps")
            .upsert(payload, on_conflict="session_id")
            .execute()
            .data
            or []
        )
        if not rows:
            raise RuntimeError("Supabase did not return the persisted session recap")
        return rows[0]

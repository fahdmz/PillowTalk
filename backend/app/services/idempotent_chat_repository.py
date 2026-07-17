"""Idempotency-enabled Supabase chat repository."""

from typing import Any

from app.services.chat_repository import SupabaseChatRepository


class IdempotentSupabaseChatRepository(SupabaseChatRepository):
    def find_idempotent_turn(
        self, session_id: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        user_rows = (
            self.supabase.table("chat_messages").select("*")
            .eq("session_id", session_id).eq("sender", "user")
            .eq("idempotency_key", idempotency_key).limit(1).execute().data or []
        )
        if not user_rows:
            return None
        user_message = user_rows[0]
        ai_rows = (
            self.supabase.table("chat_messages").select("*")
            .eq("session_id", session_id).eq("sender", "ai")
            .eq("reply_to_message_id", user_message["id"]).limit(1).execute().data or []
        )
        return {"user_message": user_message, "ai_message": ai_rows[0] if ai_rows else None}

    def reserve_idempotency_key(
        self, session_id: str, idempotency_key: str, *, text: str | None = None
    ) -> dict:
        return self._insert_linked_message({
            "session_id": session_id, "sender": "user", "text": text,
            "idempotency_key": idempotency_key,
        })

    def insert_reply(
        self, session_id: str, user_message_id: str, text: str, *, is_crisis: bool = False
    ) -> dict:
        return self._insert_linked_message({
            "session_id": session_id, "sender": "ai", "text": text,
            "is_crisis": is_crisis, "reply_to_message_id": user_message_id,
        })

    def _insert_linked_message(self, payload: dict[str, Any]) -> dict:
        rows = self.supabase.table("chat_messages").insert(payload).execute().data or []
        if not rows:
            raise RuntimeError("Supabase did not return the inserted chat message")
        return rows[0]

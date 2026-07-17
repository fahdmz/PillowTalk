import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from ..database import get_supabase
from ..deps import get_current_user_id
from ..schemas.chat import (
    ChatMessageOut,
    SendMessageRequest,
    SendMessageResponse,
    StartSessionRequest,
    StartSessionResponse,
)
from ..services.checkin_flow import greeting_for, next_step_reply
from ..services.crisis import crisis_message_fields, detect_crisis
from ..services.factors import detect_factors, record_factor_occurrence

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/start", response_model=StartSessionResponse)
def start_session(payload: StartSessionRequest, user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    session = (
        sb.table("chat_sessions")
        .insert({"user_id": user_id, "checkin_mode": payload.checkin_mode})
        .execute()
        .data[0]
    )

    greeting_row = (
        sb.table("chat_messages")
        .insert(
            {
                "session_id": session["id"],
                "sender": "ai",
                "text": greeting_for(payload.checkin_mode, payload.language),
            }
        )
        .execute()
        .data[0]
    )

    return StartSessionResponse(
        session_id=session["id"],
        checkin_mode=payload.checkin_mode,
        greeting=ChatMessageOut(**greeting_row),
    )


@router.get("/{session_id}/messages", response_model=list[ChatMessageOut])
def get_session_messages(session_id: str, user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()
    session = _get_owned_session(sb, session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    rows = (
        sb.table("chat_messages")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
        .data
        or []
    )
    return [ChatMessageOut(**row) for row in rows]


@router.post("/message", response_model=SendMessageResponse)
def send_message(payload: SendMessageRequest, user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()
    session = _get_owned_session(sb, payload.session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] == "completed":
        raise HTTPException(status_code=400, detail="This check-in has already ended")

    user_row = (
        sb.table("chat_messages")
        .insert({"session_id": session["id"], "sender": "user", "text": payload.text})
        .execute()
        .data[0]
    )

    # Deterministic, non-causal "sleep influencer" detection — never blocks
    # the reply, just logs alongside it.
    for name_key in detect_factors(payload.text):
        record_factor_occurrence(sb, user_id, name_key, session["checkin_mode"], session["id"])

    # Rule-based crisis check runs on every message and, if triggered,
    # short-circuits the fixed-step flow with the hard-stop crisis reply.
    # This is never LLM-controlled.
    if detect_crisis(payload.text):
        ai_row = (
            sb.table("chat_messages")
            .insert({"session_id": session["id"], "sender": "ai", **crisis_message_fields(payload.language)})
            .execute()
            .data[0]
        )
        sb.table("chat_sessions").update({"is_crisis": True}).eq("id", session["id"]).execute()
        return SendMessageResponse(
            user_message=ChatMessageOut(**user_row),
            ai_message=ChatMessageOut(**ai_row),
            session_status=session["status"],
        )

    step = session["step_index"]
    reply_text, is_final = next_step_reply(session["checkin_mode"], step, payload.language)

    ai_row = (
        sb.table("chat_messages")
        .insert({"session_id": session["id"], "sender": "ai", "text": reply_text})
        .execute()
        .data[0]
    )

    update_fields: dict = {"step_index": step + 1}
    new_status = session["status"]
    if is_final:
        new_status = "completed"
        update_fields["status"] = "completed"
        update_fields["ended_at"] = datetime.now(timezone.utc).isoformat()
        update_fields["preview"] = _first_user_message_preview(sb, session["id"])
        sb.table("chat_sessions").update(update_fields).eq("id", session["id"]).execute()
        if session["checkin_mode"] == "morning":
            _save_sleep_log_best_effort(sb, user_id, session["id"])
    else:
        sb.table("chat_sessions").update(update_fields).eq("id", session["id"]).execute()

    return SendMessageResponse(
        user_message=ChatMessageOut(**user_row),
        ai_message=ChatMessageOut(**ai_row),
        session_status=new_status,
    )


@router.post("/{session_id}/end", status_code=204)
def end_session_early(session_id: str, user_id: str = Depends(get_current_user_id)):
    """Lets the user close the chat (the UI's 'X' button) before the flow's
    final step — marks the session completed as-is rather than forcing the
    remaining questions."""
    sb = get_supabase()
    session = _get_owned_session(sb, session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] == "active":
        sb.table("chat_sessions").update(
            {
                "status": "completed",
                "ended_at": datetime.now(timezone.utc).isoformat(),
                "preview": _first_user_message_preview(sb, session_id),
            }
        ).eq("id", session_id).execute()


def _get_owned_session(sb, session_id: str, user_id: str) -> dict | None:
    res = (
        sb.table("chat_sessions")
        .select("*")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .execute()
    )
    rows = res.data or []
    return rows[0] if rows else None


def _first_user_message_preview(sb, session_id: str) -> str:
    rows = (
        sb.table("chat_messages")
        .select("text")
        .eq("session_id", session_id)
        .eq("sender", "user")
        .order("created_at")
        .limit(1)
        .execute()
        .data
        or []
    )
    text = rows[0]["text"] if rows and rows[0].get("text") else ""
    return text if len(text) <= 60 else text[:57] + "…"


_QUALITY_RATING_RE = re.compile(r"\b([1-5])\b")


def _save_sleep_log_best_effort(sb, user_id: str, session_id: str) -> None:
    """Best-effort extraction from the morning flow's free-text answers.
    Only the quality rating (a lone digit 1-5) is parsed reliably right now;
    bedtime/wake-time/latency parsing from free text is a follow-up (needs
    either stricter prompts or a small NLU step) and is left null until then.
    """
    rows = (
        sb.table("chat_messages")
        .select("text")
        .eq("session_id", session_id)
        .eq("sender", "user")
        .order("created_at")
        .execute()
        .data
        or []
    )
    quality_rating = None
    for row in reversed(rows):
        text = row.get("text") or ""
        match = _QUALITY_RATING_RE.search(text)
        if match:
            quality_rating = int(match.group(1))
            break

    sb.table("sleep_logs").insert(
        {
            "user_id": user_id,
            "session_id": session_id,
            "quality_rating": quality_rating,
        }
    ).execute()

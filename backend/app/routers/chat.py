import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_current_user_id
from ..schemas.chat import (
    ChatMessageOut,
    SendMessageRequest,
    SendMessageResponse,
    StartSessionRequest,
    StartSessionResponse,
)
from ..services.chat_factory import get_chat_orchestrator
from ..services.chat_orchestrator import (
    ChatOrchestrator,
    SessionCompletedError,
    SessionNotFoundError,
)
from ..services.checkin_flow import greeting_for
from ..services.recap_factory import get_recap_service
from ..services.recap_generator import RecapGenerationError
from ..services.recap_service import RecapService

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def _get_supabase() -> Any:
    from ..database import get_supabase

    return get_supabase()


def _start_of_today_utc(timezone_offset_minutes: int) -> datetime:
    """Midnight in the user's local time, expressed as a UTC instant.

    Sessions are "today's check-in" from the user's perspective, not the
    server's — using the server's own UTC day here would resume/reset
    sessions at the wrong local time for anyone outside UTC+0.
    """
    offset = timezone(timedelta(minutes=timezone_offset_minutes))
    local_now = datetime.now(timezone.utc).astimezone(offset)
    local_start = datetime(
        local_now.year, local_now.month, local_now.day, tzinfo=offset
    )
    return local_start.astimezone(timezone.utc)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_messages(sb: Any, session_id: str) -> list[dict]:
    return (
        sb.table("chat_messages")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
        .data
        or []
    )


def _insert_greeting(sb: Any, session: dict, payload: StartSessionRequest) -> dict:
    return (
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


async def _finalize_stale_session(
    sb: Any, recap_service: RecapService, user_id: str, session_id: str
) -> None:
    """Closes out a session left open from a previous day. Runs as a
    fire-and-forget background task so opening today's fresh check-in never
    has to wait on an AI recap call for yesterday's."""
    sb.table("chat_sessions").update(
        {
            "status": "completed",
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "preview": _first_user_message_preview(sb, session_id),
        }
    ).eq("id", session_id).eq("user_id", user_id).execute()
    try:
        await recap_service.generate_for_session(user_id=user_id, session_id=session_id)
    except RecapGenerationError:
        logger.exception("Best-effort recap generation failed for stale session %s", session_id)


@router.post("/start", response_model=StartSessionResponse)
async def start_session(
    payload: StartSessionRequest,
    user_id: str = Depends(get_current_user_id),
    recap_service: RecapService = Depends(get_recap_service),
):
    sb = _get_supabase()
    today_start = _start_of_today_utc(payload.timezone_offset_minutes)

    active_rows = (
        sb.table("chat_sessions")
        .select("*")
        .eq("user_id", user_id)
        .eq("checkin_mode", payload.checkin_mode)
        .eq("status", "active")
        .limit(1)
        .execute()
        .data
        or []
    )

    if active_rows:
        session = active_rows[0]
        if _parse_timestamp(session["started_at"]) >= today_start:
            # Still open from earlier today — resume it with full history.
            messages = _load_messages(sb, session["id"])
            if not messages:
                messages = [_insert_greeting(sb, session, payload)]
            return StartSessionResponse(
                session_id=session["id"],
                checkin_mode=payload.checkin_mode,
                session_status=session["status"],
                messages=[ChatMessageOut(**m) for m in messages],
            )
        # Left active from a previous day — close it out in the background
        # and fall through to start a fresh session for today.
        asyncio.create_task(
            _finalize_stale_session(sb, recap_service, user_id, session["id"])
        )
    else:
        # No active session — see if today's check-in of this type already
        # ran to completion; if so, that's today's one-per-day slot used.
        today_rows = (
            sb.table("chat_sessions")
            .select("*")
            .eq("user_id", user_id)
            .eq("checkin_mode", payload.checkin_mode)
            .gte("started_at", today_start.isoformat())
            .order("started_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        if today_rows:
            session = today_rows[0]
            messages = _load_messages(sb, session["id"])
            return StartSessionResponse(
                session_id=session["id"],
                checkin_mode=payload.checkin_mode,
                session_status=session["status"],
                messages=[ChatMessageOut(**m) for m in messages],
            )

    session = (
        sb.table("chat_sessions")
        .insert({"user_id": user_id, "checkin_mode": payload.checkin_mode})
        .execute()
        .data[0]
    )
    greeting_row = _insert_greeting(sb, session, payload)
    return StartSessionResponse(
        session_id=session["id"],
        checkin_mode=payload.checkin_mode,
        session_status=session["status"],
        messages=[ChatMessageOut(**greeting_row)],
    )


@router.get("/{session_id}/messages", response_model=list[ChatMessageOut])
def get_session_messages(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
):
    sb = _get_supabase()
    if _get_owned_session(sb, session_id, user_id) is None:
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
async def send_message(
    payload: SendMessageRequest,
    user_id: str = Depends(get_current_user_id),
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    try:
        result = await orchestrator.send_message(
            user_id=user_id,
            session_id=payload.session_id,
            text=payload.text,
            language=payload.language,
        )
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    except SessionCompletedError as exc:
        raise HTTPException(
            status_code=400, detail="This check-in has already ended"
        ) from exc

    return SendMessageResponse(
        user_message=ChatMessageOut(**result.user_message),
        ai_message=ChatMessageOut(**result.ai_message),
        session_status=result.session_status,
    )


@router.post("/{session_id}/end", status_code=204)
async def end_session_early(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    recap_service: RecapService = Depends(get_recap_service),
):
    sb = _get_supabase()
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
        ).eq("id", session_id).eq("user_id", user_id).execute()

    try:
        await recap_service.generate_for_session(
            user_id=user_id,
            session_id=session_id,
        )
    except RecapGenerationError as exc:
        raise HTTPException(
            status_code=503,
            detail="Recap generation is temporarily unavailable",
            headers={"Retry-After": "2"},
        ) from exc


def _get_owned_session(sb: Any, session_id: str, user_id: str) -> dict | None:
    rows = (
        sb.table("chat_sessions")
        .select("*")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .execute()
        .data
        or []
    )
    return rows[0] if rows else None


def _first_user_message_preview(sb: Any, session_id: str) -> str:
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
    text = rows[0].get("text", "") if rows else ""
    return text if len(text) <= 60 else f"{text[:57]}…"

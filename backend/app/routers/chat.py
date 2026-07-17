from datetime import datetime, timezone
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


def _get_supabase() -> Any:
    from ..database import get_supabase

    return get_supabase()


@router.post("/start", response_model=StartSessionResponse)
def start_session(
    payload: StartSessionRequest,
    user_id: str = Depends(get_current_user_id),
):
    sb = _get_supabase()
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
        greeting_rows = (
            sb.table("chat_messages")
            .select("*")
            .eq("session_id", session["id"])
            .eq("sender", "ai")
            .order("created_at")
            .limit(1)
            .execute()
            .data
            or []
        )
    else:
        session = (
            sb.table("chat_sessions")
            .insert({"user_id": user_id, "checkin_mode": payload.checkin_mode})
            .execute()
            .data[0]
        )
        greeting_rows = []

    if greeting_rows:
        greeting_row = greeting_rows[0]
    else:
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

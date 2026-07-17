from datetime import datetime
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_current_user_id
from ..schemas.chat import ChatMessageOut
from ..schemas.recap import RecapDetail, RecapListItem

router = APIRouter(prefix="/recaps", tags=["recaps"])


def get_supabase() -> Any:
    from ..database import get_supabase as get_database_client

    return get_database_client()


@router.get("", response_model=list[RecapListItem])
def list_recaps(
    filter: Literal["all", "night", "morning"] = "all",
    month: Optional[str] = Query(None, description="YYYY-MM, filters to that month"),
    user_id: str = Depends(get_current_user_id),
):
    sb = get_supabase()
    q = (
        sb.table("session_recaps")
        .select(
            "id,session_id,title,summary,dominant_emotion,domains,generated_at,"
            "chat_sessions!inner(id,user_id,started_at,checkin_mode,preview,status)"
        )
        .eq("chat_sessions.user_id", user_id)
        .eq("chat_sessions.status", "completed")
        .order("generated_at", desc=True)
    )
    if filter != "all":
        q = q.eq("chat_sessions.checkin_mode", filter)
    if month:
        q = q.gte("chat_sessions.started_at", f"{month}-01").lt(
            "chat_sessions.started_at", f"{_next_month(month)}-01"
        )
    rows = q.execute().data or []

    return [_list_item(row) for row in rows]


@router.get("/{recap_id}", response_model=RecapDetail)
def get_recap(recap_id: str, user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()
    rows = (
        sb.table("session_recaps")
        .select(
            "*,chat_sessions!inner("
            "id,user_id,started_at,checkin_mode,preview,status)"
        )
        .eq("id", recap_id)
        .eq("chat_sessions.user_id", user_id)
        .eq("chat_sessions.status", "completed")
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Recap not found")
    recap = rows[0]
    session = _embedded_session(recap)

    messages = (
        sb.table("chat_messages")
        .select("*")
        .eq("session_id", session["id"])
        .order("created_at")
        .execute()
        .data
        or []
    )
    item = _list_item(recap)
    return RecapDetail(
        **item.model_dump(),
        conclusion=recap.get("conclusion"),
        emotional_trend=recap.get("emotional_trend") or {},
        sleep_observations=recap.get("sleep_observations") or [],
        generated_at=recap.get("generated_at"),
        transcript=[ChatMessageOut(**message) for message in messages],
    )


@router.delete("/{recap_id}", status_code=204)
def delete_recap(recap_id: str, user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()
    rows = (
        sb.table("session_recaps")
        .select("session_id,chat_sessions!inner(user_id)")
        .eq("id", recap_id)
        .eq("chat_sessions.user_id", user_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Recap not found")
    sb.table("chat_sessions").delete().eq("id", rows[0]["session_id"]).eq(
        "user_id", user_id
    ).execute()


def _list_item(recap: dict[str, Any]) -> RecapListItem:
    session = _embedded_session(recap)
    return RecapListItem(
        id=recap["id"],
        session_id=session["id"],
        date=session["started_at"][:10],
        time=_format_time(session["started_at"]),
        is_night=session["checkin_mode"] == "night",
        preview=session.get("preview"),
        title=recap.get("title"),
        summary=recap.get("summary"),
        dominant_emotion=recap.get("dominant_emotion"),
        domains=recap.get("domains") or [],
    )


def _embedded_session(recap: dict[str, Any]) -> dict[str, Any]:
    session = recap.get("chat_sessions")
    if isinstance(session, list):
        session = session[0] if session else None
    if not isinstance(session, dict):
        raise RuntimeError("Supabase did not return the recap's chat session")
    return session


def _format_time(iso_ts: str) -> str:
    dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    hour12 = dt.strftime("%I").lstrip("0") or "12"
    return f"{hour12}:{dt.strftime('%M %p')}"


def _next_month(month: str) -> str:
    year, mon = (int(part) for part in month.split("-"))
    return f"{year + 1}-01" if mon == 12 else f"{year}-{mon + 1:02d}"

from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import get_supabase
from ..deps import get_current_user_id
from ..schemas.chat import ChatMessageOut
from ..schemas.recap import RecapDetail, RecapListItem

router = APIRouter(prefix="/recaps", tags=["recaps"])


@router.get("", response_model=list[RecapListItem])
def list_recaps(
    filter: Literal["all", "night", "morning"] = "all",
    month: Optional[str] = Query(None, description="YYYY-MM, filters to that month"),
    user_id: str = Depends(get_current_user_id),
):
    sb = get_supabase()
    q = (
        sb.table("chat_sessions")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "completed")
        .order("started_at", desc=True)
    )
    if filter != "all":
        q = q.eq("checkin_mode", filter)
    if month:
        q = q.gte("started_at", f"{month}-01").lt("started_at", f"{_next_month(month)}-01")
    rows = q.execute().data or []

    return [
        RecapListItem(
            id=row["id"],
            date=row["started_at"][:10],
            time=_format_time(row["started_at"]),
            is_night=row["checkin_mode"] == "night",
            preview=row.get("preview"),
        )
        for row in rows
    ]


@router.get("/{recap_id}", response_model=RecapDetail)
def get_recap(recap_id: str, user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()
    rows = (
        sb.table("chat_sessions")
        .select("*")
        .eq("id", recap_id)
        .eq("user_id", user_id)
        .execute()
        .data
        or []
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Recap not found")
    session = rows[0]

    messages = (
        sb.table("chat_messages")
        .select("*")
        .eq("session_id", recap_id)
        .order("created_at")
        .execute()
        .data
        or []
    )

    return RecapDetail(
        id=session["id"],
        date=session["started_at"][:10],
        time=_format_time(session["started_at"]),
        is_night=session["checkin_mode"] == "night",
        transcript=[ChatMessageOut(**m) for m in messages],
    )


@router.delete("/{recap_id}", status_code=204)
def delete_recap(recap_id: str, user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()
    rows = (
        sb.table("chat_sessions")
        .select("id")
        .eq("id", recap_id)
        .eq("user_id", user_id)
        .execute()
        .data
        or []
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Recap not found")
    sb.table("chat_sessions").delete().eq("id", recap_id).execute()


def _format_time(iso_ts: str) -> str:
    dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    hour12 = dt.strftime("%I").lstrip("0") or "12"
    return f"{hour12}:{dt.strftime('%M %p')}"


def _next_month(month: str) -> str:
    year, mon = (int(part) for part in month.split("-"))
    return f"{year + 1}-01" if mon == 12 else f"{year}-{mon + 1:02d}"

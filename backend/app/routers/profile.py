from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from ..database import get_supabase
from ..deps import get_current_user_claims, get_current_user_id
from ..schemas.profile import (
    ProfileOut,
    ProfilePatch,
    SleepFactorOut,
    SleepOccurrenceOut,
    SleepStatsOut,
    WeeklySleepOut,
)

router = APIRouter(prefix="/profile", tags=["profile"])

# Computed from checkin_date.weekday() rather than strftime('%a') so the
# abbreviation doesn't depend on the server's locale.
_WEEKDAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@router.get("", response_model=ProfileOut)
def get_profile(claims: dict = Depends(get_current_user_claims)):
    sb = get_supabase()
    user_id = claims["sub"]
    rows = sb.table("profiles").select("*").eq("id", user_id).execute().data
    if not rows:
        full_name = (claims.get("user_metadata") or {}).get("full_name")
        rows = sb.table("profiles").insert({"id": user_id, "full_name": full_name}).execute().data
    return ProfileOut(**rows[0])


@router.patch("", response_model=ProfileOut)
def update_profile(payload: ProfilePatch, user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()
    updates = payload.model_dump(exclude_unset=True)
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    existing = sb.table("profiles").select("id").eq("id", user_id).execute().data
    if existing:
        rows = sb.table("profiles").update(updates).eq("id", user_id).execute().data
    else:
        rows = sb.table("profiles").insert({"id": user_id, **updates}).execute().data
    return ProfileOut(**rows[0])


@router.get("/sleep/weekly", response_model=SleepStatsOut)
def get_weekly_sleep(user_id: str = Depends(get_current_user_id)):
    """NOTE: avg_sleep_time / avg_wake_time currently return the most recent
    logged value, not a true average — averaging clock times across midnight
    needs a circular mean and is a follow-up, not implemented yet."""
    sb = get_supabase()
    since = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    rows = (
        sb.table("sleep_logs")
        .select("*")
        .eq("user_id", user_id)
        .gte("checkin_date", since)
        .order("checkin_date")
        .execute()
        .data
        or []
    )

    week = [
        WeeklySleepOut(
            day=_WEEKDAY_ABBR[datetime.fromisoformat(row["checkin_date"]).weekday()],
            hours=round((row.get("duration_minutes") or 0) / 60, 1),
        )
        for row in rows
    ]
    bedtimes = [row["bedtime"] for row in rows if row.get("bedtime")]
    wake_times = [row["wake_time"] for row in rows if row.get("wake_time")]

    return SleepStatsOut(
        week=week,
        avg_sleep_time=bedtimes[-1] if bedtimes else None,
        avg_wake_time=wake_times[-1] if wake_times else None,
    )


@router.get("/sleep-factors", response_model=list[SleepFactorOut])
def get_sleep_factors(user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()
    factors = sb.table("sleep_factors").select("*").eq("user_id", user_id).execute().data or []

    out = []
    for factor in factors:
        occurrences = (
            sb.table("sleep_factor_occurrences")
            .select("*")
            .eq("factor_id", factor["id"])
            .order("occurred_at", desc=True)
            .limit(5)
            .execute()
            .data
            or []
        )
        out.append(
            SleepFactorOut(
                name_key=factor["name_key"],
                level=factor["level"],
                occurrences=[
                    SleepOccurrenceOut(checkin_label_key=o["checkin_label_key"], time=o["occurred_at"])
                    for o in occurrences
                ],
            )
        )
    return out

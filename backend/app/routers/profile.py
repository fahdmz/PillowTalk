from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query

from ..deps import get_current_user_claims, get_current_user_id
from ..schemas.profile import (
    ProfileOut,
    ProfilePatch,
    SleepFactorOut,
    SleepOccurrenceOut,
    SleepStatsOut,
)
from ..services.dashboard import (
    SupabaseDashboardRepository,
    build_weekly_sleep_dashboard,
)

router = APIRouter(prefix="/profile", tags=["profile"])


def get_supabase() -> Any:
    from ..database import get_supabase as get_database_client

    return get_database_client()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@router.get("", response_model=ProfileOut)
def get_profile(claims: dict = Depends(get_current_user_claims)):
    sb = get_supabase()
    user_id = claims["sub"]
    rows = sb.table("profiles").select("*").eq("id", user_id).execute().data
    if not rows:
        full_name = (claims.get("user_metadata") or {}).get("full_name")
        # PillowTalk is an Indonesian-first product — default new profiles to
        # "id" explicitly rather than relying on the database column default.
        rows = (
            sb.table("profiles")
            .insert({"id": user_id, "full_name": full_name, "language": "id"})
            .execute()
            .data
        )
    return ProfileOut(**rows[0])


@router.patch("", response_model=ProfileOut)
def update_profile(
    payload: ProfilePatch,
    user_id: str = Depends(get_current_user_id),
):
    sb = get_supabase()
    updates = payload.model_dump(exclude_unset=True)
    updates["updated_at"] = _now_utc().isoformat()

    existing = sb.table("profiles").select("id").eq("id", user_id).execute().data
    if existing:
        rows = sb.table("profiles").update(updates).eq("id", user_id).execute().data
    else:
        rows = (
            sb.table("profiles")
            .insert({"id": user_id, **updates})
            .execute()
            .data
        )
    return ProfileOut(**rows[0])


@router.get("/sleep/weekly", response_model=SleepStatsOut)
def get_weekly_sleep(
    days: int = Query(7, ge=2, le=30),
    timezone_offset_minutes: int = Query(420, ge=-720, le=840),
    user_id: str = Depends(get_current_user_id),
):
    now = _now_utc()
    since = _local_window_start(
        now=now,
        days=days,
        timezone_offset_minutes=timezone_offset_minutes,
    )
    analyses = SupabaseDashboardRepository(get_supabase()).load_sleep_analyses(
        user_id=user_id,
        since=since,
    )
    return SleepStatsOut(
        **build_weekly_sleep_dashboard(
            analyses,
            now=now,
            timezone_offset_minutes=timezone_offset_minutes,
            days=days,
        )
    )


@router.get("/sleep-factors", response_model=list[SleepFactorOut])
def get_sleep_factors(
    days: int = Query(30, ge=7, le=90),
    timezone_offset_minutes: int = Query(420, ge=-720, le=840),
    user_id: str = Depends(get_current_user_id),
):
    since = _local_window_start(
        now=_now_utc(),
        days=days,
        timezone_offset_minutes=timezone_offset_minutes,
    )
    rows = SupabaseDashboardRepository(get_supabase()).load_sleep_factors(
        user_id=user_id,
        since=since,
    )
    return [
        SleepFactorOut(
            name_key=row["name_key"],
            level=row["level"],
            trend_status=row["trend_status"],
            sample_size=row["sample_size"],
            mean_confidence=row["mean_confidence"],
            interpretation=row["interpretation"],
            occurrences=[
                SleepOccurrenceOut(
                    checkin_label_key=occurrence["checkin_label_key"],
                    time=occurrence["occurred_at"],
                    evidence_kind=occurrence.get("evidence_kind"),
                    source=occurrence.get("source"),
                    confidence=occurrence.get("confidence"),
                )
                for occurrence in row["occurrences"]
            ],
        )
        for row in rows
    ]


def _local_window_start(
    *,
    now: datetime,
    days: int,
    timezone_offset_minutes: int,
) -> datetime:
    offset = timezone(timedelta(minutes=timezone_offset_minutes))
    local_now = now.astimezone(offset)
    local_start_date = local_now.date() - timedelta(days=days - 1)
    local_start = datetime.combine(local_start_date, datetime.min.time(), offset)
    return local_start.astimezone(timezone.utc)

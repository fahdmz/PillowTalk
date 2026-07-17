"""Dashboard read models aggregated from owned Supabase source rows."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

_WEEKDAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class SupabaseDashboardRepository:
    def __init__(self, supabase: Any) -> None:
        self.supabase = supabase

    def load_sleep_analyses(
        self,
        *,
        user_id: str,
        since: datetime,
    ) -> list[dict[str, Any]]:
        sessions = (
            self.supabase.table("chat_sessions")
            .select("id")
            .eq("user_id", user_id)
            .execute()
            .data
            or []
        )
        session_ids = [session["id"] for session in sessions]
        if not session_ids:
            return []
        return (
            self.supabase.table("message_analyses")
            .select(
                "session_id,sleep_hours,wake_time,source,confidence,created_at"
            )
            .in_("session_id", session_ids)
            .gte("created_at", since.isoformat())
            .order("created_at")
            .execute()
            .data
            or []
        )

    def load_sleep_factors(
        self,
        *,
        user_id: str,
        since: datetime,
    ) -> list[dict[str, Any]]:
        factors = (
            self.supabase.table("sleep_factors")
            .select("id,name_key")
            .eq("user_id", user_id)
            .execute()
            .data
            or []
        )
        factor_ids = [factor["id"] for factor in factors]
        if not factor_ids:
            return []
        occurrences = (
            self.supabase.table("sleep_factor_occurrences")
            .select(
                "factor_id,checkin_label_key,occurred_at,evidence_kind,"
                "source,confidence"
            )
            .in_("factor_id", factor_ids)
            .gte("occurred_at", since.isoformat())
            .order("occurred_at", desc=True)
            .execute()
            .data
            or []
        )
        return build_factor_dashboard(factors, occurrences)


def build_factor_dashboard(
    factors: list[dict[str, Any]],
    occurrences: list[dict[str, Any]],
    *,
    minimum_samples: int = 2,
    occurrence_preview_limit: int = 5,
) -> list[dict[str, Any]]:
    by_factor: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for occurrence in occurrences:
        by_factor[occurrence["factor_id"]].append(occurrence)

    output = []
    for factor in factors:
        source_rows = sorted(
            by_factor.get(factor["id"], []),
            key=lambda row: row["occurred_at"],
            reverse=True,
        )
        sample_size = len(source_rows)
        if sample_size == 0:
            continue
        confidence_values = [
            float(row["confidence"])
            for row in source_rows
            if row.get("confidence") is not None
        ]
        output.append(
            {
                "name_key": factor["name_key"],
                "level": _factor_level(sample_size),
                "trend_status": (
                    "observed"
                    if sample_size >= minimum_samples
                    else "insufficient_data"
                ),
                "sample_size": sample_size,
                "mean_confidence": (
                    round(sum(confidence_values) / len(confidence_values), 3)
                    if confidence_values
                    else None
                ),
                "interpretation": "observed_alongside_checkins",
                "occurrences": source_rows[:occurrence_preview_limit],
            }
        )
    return sorted(output, key=lambda row: (-row["sample_size"], row["name_key"]))


def build_weekly_sleep_dashboard(
    analyses: list[dict[str, Any]],
    *,
    now: datetime,
    timezone_offset_minutes: int,
    days: int = 7,
    minimum_samples: int = 2,
) -> dict[str, Any]:
    offset = timezone(timedelta(minutes=timezone_offset_minutes))
    local_today = now.astimezone(offset).date()
    first_day = local_today - timedelta(days=days - 1)
    latest_by_day: dict[date, dict[str, Any]] = {}
    for analysis in sorted(analyses, key=lambda row: row["created_at"]):
        if analysis.get("sleep_hours") is None:
            continue
        created_at = datetime.fromisoformat(
            analysis["created_at"].replace("Z", "+00:00")
        )
        local_day = created_at.astimezone(offset).date()
        if first_day <= local_day <= local_today:
            latest_by_day[local_day] = analysis

    source_rows = [latest_by_day[day] for day in sorted(latest_by_day)]
    hours = [float(row["sleep_hours"]) for row in source_rows]
    wake_minutes = [
        _clock_minutes(row["wake_time"])
        for row in source_rows
        if row.get("wake_time")
    ]
    bed_minutes = [
        (_clock_minutes(row["wake_time"]) - float(row["sleep_hours"]) * 60)
        % 1440
        for row in source_rows
        if row.get("wake_time")
    ]
    sample_size = len(source_rows)
    return {
        "week": [
            {
                "day": _WEEKDAY_ABBR[day.weekday()],
                "hours": round(float(latest_by_day[day]["sleep_hours"]), 1),
            }
            for day in sorted(latest_by_day)
        ],
        "avg_sleep_hours": round(sum(hours) / sample_size, 1) if hours else None,
        "avg_sleep_time": _format_clock(_circular_mean(bed_minutes)),
        "avg_wake_time": _format_clock(_circular_mean(wake_minutes)),
        "sample_size": sample_size,
        "trend_status": (
            "observed" if sample_size >= minimum_samples else "insufficient_data"
        ),
    }


def _factor_level(sample_size: int) -> str:
    if sample_size >= 3:
        return "high"
    if sample_size == 2:
        return "medium"
    return "low"


def _clock_minutes(value: str) -> int:
    hour, minute = (int(part) for part in value[:5].split(":"))
    return hour * 60 + minute


def _circular_mean(values: list[float]) -> int | None:
    if not values:
        return None
    radians = [value / 1440 * 2 * math.pi for value in values]
    angle = math.atan2(
        sum(math.sin(value) for value in radians),
        sum(math.cos(value) for value in radians),
    )
    return round((angle % (2 * math.pi)) / (2 * math.pi) * 1440) % 1440


def _format_clock(minutes: int | None) -> str | None:
    if minutes is None:
        return None
    return f"{minutes // 60:02d}:{minutes % 60:02d}"

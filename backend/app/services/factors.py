"""Deterministic 'sleep influencer' detection.

Keyword matching only, on purpose — the Profile tab presents these as
non-causal, auto-detected observations ("logged alongside these check-ins"),
never as a diagnosis or a causal claim. If this ever needs real NLP, the
non-causal framing in the frontend copy has to be preserved.
"""

from datetime import datetime, timezone

from supabase import Client

CheckinMode = str

_FACTOR_KEYWORDS: dict[str, list[str]] = {
    "Late caffeine intake": ["coffee", "caffeine", "kopi", "kafein"],
    "Screen time before bed": [
        "phone", "scrolling", "scroll", "screen", "ponsel", "layar", "media sosial", "hp",
    ],
    "Work-related stress": [
        "work", "deadline", "meeting", "presentation", "kerja", "rapat", "pekerjaan", "presentasi",
    ],
    "Irregular bedtime schedule": [
        "late night", "irregular", "jadwal", "begadang", "tidur larut",
    ],
}

_CHECKIN_LABEL: dict[CheckinMode, str] = {
    "night": "Nightly Check-in",
    "morning": "Morning Check-in",
}


def detect_factors(text: str) -> list[str]:
    lowered = text.lower()
    return [name for name, keywords in _FACTOR_KEYWORDS.items() if any(kw in lowered for kw in keywords)]


def record_factor_occurrence(sb: Client, user_id: str, name_key: str, checkin_mode: CheckinMode, session_id: str) -> None:
    """Upserts the factor row for this user and logs one occurrence, then
    recomputes level from a simple occurrence count (>=3 high, 2 medium,
    else low) rather than anything causal."""
    existing = (
        sb.table("sleep_factors")
        .select("id")
        .eq("user_id", user_id)
        .eq("name_key", name_key)
        .execute()
        .data
    )
    if existing:
        factor_id = existing[0]["id"]
    else:
        inserted = (
            sb.table("sleep_factors")
            .insert({"user_id": user_id, "name_key": name_key, "level": "low"})
            .execute()
            .data
        )
        factor_id = inserted[0]["id"]

    sb.table("sleep_factor_occurrences").insert(
        {
            "factor_id": factor_id,
            "session_id": session_id,
            "checkin_label_key": _CHECKIN_LABEL.get(checkin_mode, "Nightly Check-in"),
        }
    ).execute()

    count_res = (
        sb.table("sleep_factor_occurrences")
        .select("id", count="exact")
        .eq("factor_id", factor_id)
        .execute()
    )
    count = count_res.count or 0
    level = "high" if count >= 3 else "medium" if count == 2 else "low"
    sb.table("sleep_factors").update(
        {"level": level, "updated_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", factor_id).execute()

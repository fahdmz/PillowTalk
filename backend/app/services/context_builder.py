"""Build a bounded, non-diagnostic chatbot memory payload."""

from collections import Counter
from typing import Any


def build_chat_context(
    *,
    messages: list[dict[str, Any]],
    recaps: list[dict[str, Any]],
    analyses: list[dict[str, Any]],
    message_limit: int,
    recap_limit: int,
) -> dict[str, Any]:
    emotion_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    substance_counts: Counter[str] = Counter()
    reported_sleep_hours: list[float] = []

    for analysis in analyses:
        emotion = analysis.get("emotion")
        if emotion:
            emotion_counts[str(emotion)] += 1
        domain_counts.update(str(value) for value in analysis.get("domains") or [])
        substance_counts.update(
            str(value) for value in analysis.get("sleep_substances") or []
        )
        sleep_hours = analysis.get("sleep_hours")
        if sleep_hours is not None:
            reported_sleep_hours.append(float(sleep_hours))

    return {
        "recent_messages": messages[-message_limit:],
        "recent_recaps": recaps[:recap_limit],
        "emotional_trends": {
            "sample_size": len(analyses),
            "emotion_counts": dict(emotion_counts),
            "domain_counts": dict(domain_counts),
            "sleep_substance_counts": dict(substance_counts),
            "reported_sleep_hours": reported_sleep_hours,
        },
    }

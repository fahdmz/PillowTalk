"""Seed (and clean up) realistic chat/analysis rows directly in Supabase, to
exercise the dashboard/statistics pipeline — weekly sleep chart, sleep-factor
leveling, and the recap list/detail — without needing days of real check-ins.

This intentionally does NOT test the ML emotion classifier: `emotion` and
`confidence` below are hand-picked, not model output. Domains, substances,
sleep_hours, and wake_time ARE run through the real
`app.services.analysis_normalizer.extract_context`, so those fields are
exactly what the live pipeline would have extracted from the same text. To
actually exercise the classifier, send the messages in
backend/tests/manual_test_conversations.md through the real /chat endpoints
instead — this script is for the statistics layer only.

This writes to your real Supabase project via the service-role key in
backend/.env — the same credential the backend server uses. Always run
--dry-run first. Every row this script inserts is recorded in a manifest
file so it can be cleanly removed with --cleanup later.

Usage:
    cd backend
    source .venv/bin/activate
    python -m scripts.seed_stats_test_data --email you@example.com --dry-run
    python -m scripts.seed_stats_test_data --email you@example.com
    python -m scripts.seed_stats_test_data --cleanup scripts/seed_manifests/<file>.json
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_supabase  # noqa: E402
from app.services.analysis_normalizer import extract_context  # noqa: E402

MANIFEST_DIR = Path(__file__).resolve().parent / "seed_manifests"

# Jakarta is UTC+7. Keeping local hours away from the 00:00/24:00 boundary
# means `local_time - 7h` never rolls over to a different UTC calendar date,
# so these timestamps land on the intended day in both UTC and the
# dashboard's default `timezone_offset_minutes=420` (Asia/Jakarta) view.
_NIGHT_LOCAL_HOUR = 22
_MORNING_LOCAL_HOUR = 7
_TZ_OFFSET_HOURS = 7


@dataclass
class Turn:
    text: str
    emotion: str
    confidence: float
    source: str = "local"


@dataclass
class SessionSpec:
    day_offset: int  # 0 = tonight/this morning, larger = further in the past
    mode: Literal["night", "morning"]
    turns: list[Turn]
    ai_reply: str


# Reuses the same kinds of lines as backend/tests/manual_test_conversations.md
# so the two test paths (real pipeline vs. direct injection) describe a
# consistent story — caffeine/work show up often enough to reach the "high"
# sleep-factor level (3+ occurrences), alcohol only once ("low").
_SESSIONS: list[SessionSpec] = [
    SessionSpec(
        day_offset=6,
        mode="night",
        ai_reply="That sounds like it's been weighing on you. Want to tell me more?",
        turns=[
            Turn(
                "I had a coffee after 6pm because of a work deadline and now my head won't stop racing.",
                emotion="sadness",
                confidence=0.78,
            ),
        ],
    ),
    SessionSpec(
        day_offset=6,
        mode="morning",
        ai_reply="Thanks for sharing. What time did you get into bed, and about how long did it take to fall asleep?",
        turns=[
            Turn(
                "I slept for 6 hours total and woke up at 6:45, felt pretty rough.",
                emotion="sadness",
                confidence=0.71,
            ),
        ],
    ),
    SessionSpec(
        day_offset=5,
        mode="night",
        ai_reply="I hear you. Sometimes naming it helps it feel lighter. Anything else on your mind?",
        turns=[
            Turn(
                "Good day today actually, I'm really happy — we closed out a project early. Had a coffee around 8pm to celebrate though.",
                emotion="joy",
                confidence=0.83,
            ),
        ],
    ),
    SessionSpec(
        day_offset=4,
        mode="night",
        ai_reply="That sounds like it's been weighing on you. Want to tell me more?",
        turns=[
            Turn(
                "I'm honestly furious. My manager moved the deadline up again and I have a headache from the stress.",
                emotion="anger",
                confidence=0.8,
            ),
        ],
    ),
    SessionSpec(
        day_offset=4,
        mode="morning",
        ai_reply="Got it. Did you wake up during the night? If so, about how many times, and for how long in total?",
        turns=[
            Turn(
                "I slept for 7 hours and woke up at 6, feeling pretty neutral about the day ahead.",
                emotion="neutral",
                confidence=0.66,
            ),
        ],
    ),
    SessionSpec(
        day_offset=3,
        mode="night",
        ai_reply="Thank you for sharing that. Let's set it down for tonight.",
        turns=[
            Turn(
                "Had a couple glasses of wine with my partner tonight, and I also smoked a cigarette outside which I'm not proud of.",
                emotion="fear",
                confidence=0.69,
            ),
        ],
    ),
    SessionSpec(
        day_offset=2,
        mode="night",
        ai_reply="That sounds like it's been weighing on you. Want to tell me more?",
        turns=[
            Turn(
                "Another coffee after dinner because of work again, I really need to stop doing this before bed.",
                emotion="sadness",
                confidence=0.74,
            ),
        ],
    ),
    SessionSpec(
        day_offset=2,
        mode="morning",
        ai_reply="Thanks. What time did you finally wake up, and how would you rate your sleep quality?",
        turns=[
            Turn(
                "I slept for 5 hours, woke up at 5:30, and my body still feels tired.",
                emotion="sadness",
                confidence=0.7,
            ),
        ],
    ),
    SessionSpec(
        day_offset=1,
        mode="night",
        ai_reply="I hear you. Sometimes naming it helps it feel lighter. Anything else on your mind?",
        turns=[
            Turn(
                "I took melatonin again tonight because I'm scared I won't fall asleep like last week. "
                "Also had a glass of wine before bed.",
                emotion="fear",
                confidence=0.72,
            ),
        ],
    ),
    SessionSpec(
        day_offset=0,
        mode="morning",
        ai_reply="That's really useful, thank you. Have a gentle day.",
        turns=[
            Turn(
                "No coffee, no alcohol yesterday, just a normal quiet evening. I slept for 8 hours and woke up at 7.",
                emotion="neutral",
                confidence=0.68,
            ),
        ],
    ),
]

_CHECKIN_LABEL = {"night": "Nightly Check-in", "morning": "Morning Check-in"}
_TREND_DIRECTIONS = {
    "joy": "membaik",
    "love": "membaik",
    "neutral": "stabil",
    "surprise": "stabil",
    "sadness": "memburuk",
    "anger": "memburuk",
    "fear": "memburuk",
}


@dataclass
class Manifest:
    user_id: str
    created_at: str
    chat_session_ids: list[str] = field(default_factory=list)
    sleep_factor_occurrence_ids: list[str] = field(default_factory=list)
    sleep_factor_ids_created: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "created_at": self.created_at,
            "chat_session_ids": self.chat_session_ids,
            "sleep_factor_occurrence_ids": self.sleep_factor_occurrence_ids,
            "sleep_factor_ids_created": self.sleep_factor_ids_created,
        }


def resolve_user_id(sb: Any, *, email: str | None, user_id: str | None) -> str:
    if user_id:
        return user_id
    if not email:
        raise SystemExit("Pass --email or --user-id so seeded rows attach to your account.")
    email_lower = email.strip().casefold()
    for page in range(1, 21):
        users = sb.auth.admin.list_users(page=page, per_page=200)
        if not users:
            break
        for user in users:
            if (user.email or "").casefold() == email_lower:
                return user.id
    raise SystemExit(f"No Supabase auth user found with email {email!r}.")


def _utc_timestamp(day_offset: int, mode: Literal["night", "morning"], *, anchor: datetime) -> datetime:
    local_hour = _NIGHT_LOCAL_HOUR if mode == "night" else _MORNING_LOCAL_HOUR
    local_day = anchor - timedelta(days=day_offset)
    local_dt = local_day.replace(hour=local_hour, minute=0, second=0, microsecond=0)
    return local_dt - timedelta(hours=_TZ_OFFSET_HOURS)


def _factor_keys_for(domains: list[str], substances: list[str]) -> list[str]:
    keys = [d for d in domains if d != "sleep_substances"]
    keys.extend(substances)
    seen = dict.fromkeys(keys)
    return list(seen)


def _build_recap(mode: str, turns_data: list[dict[str, Any]]) -> dict[str, Any]:
    domains = sorted({d for t in turns_data for d in t["domains"]})
    substances = sorted({s for t in turns_data for s in t["substances"]})
    emotions = [t["emotion"] for t in turns_data]
    dominant = max(set(emotions), key=emotions.count)
    sleep_hours = next((t["sleep_hours"] for t in turns_data if t["sleep_hours"] is not None), None)
    wake_time = next((t["wake_time"] for t in turns_data if t["wake_time"] is not None), None)

    observations = []
    if sleep_hours is not None:
        observations.append(f"Tidur sekitar {sleep_hours} jam semalam.")
    if wake_time is not None:
        observations.append(f"Bangun sekitar pukul {wake_time}.")
    if substances:
        observations.append("Menyebutkan " + ", ".join(substances) + " di sekitar waktu tidur.")

    label = "malam" if mode == "night" else "pagi"
    return {
        "title": f"[seed] Catatan check-in {label}",
        "summary": (
            f"[seed] Ringkasan otomatis untuk pengujian statistik — check-in {label} ini "
            f"menyentuh domain: {', '.join(domains) if domains else 'tidak ada domain spesifik'}."
        ),
        "conclusion": "[seed] Data pengujian — bukan rangkuman yang dihasilkan AI.",
        "dominant_emotion": dominant,
        "domains": domains,
        "emotional_trend": {
            "direction": _TREND_DIRECTIONS.get(dominant, "tidak_cukup_data"),
            "observation": "[seed] Observasi otomatis untuk data pengujian.",
        },
        "sleep_observations": observations,
        "model_deployment": "seed-script",
        "prompt_version": "seed-v1",
    }


def build_rows(user_id: str, *, anchor: datetime) -> list[dict[str, Any]]:
    """Returns one plan entry per SessionSpec with everything pre-computed
    (but not yet inserted) so --dry-run can print it without touching the DB."""
    plan = []
    for spec in _SESSIONS:
        started_at = _utc_timestamp(spec.day_offset, spec.mode, anchor=anchor)
        turns_data = []
        for turn in spec.turns:
            extracted = extract_context(turn.text)
            turns_data.append(
                {
                    "text": turn.text,
                    "emotion": turn.emotion,
                    "confidence": turn.confidence,
                    "source": turn.source,
                    "domains": [d.value for d in extracted.domains],
                    "substances": [s.value for s in extracted.sleep_substances],
                    "sleep_hours": extracted.sleep_hours,
                    "wake_time": extracted.wake_time,
                }
            )
        plan.append(
            {
                "user_id": user_id,
                "mode": spec.mode,
                "started_at": started_at,
                "ended_at": started_at + timedelta(minutes=6),
                "ai_reply": spec.ai_reply,
                "turns": turns_data,
                "recap": _build_recap(spec.mode, turns_data),
            }
        )
    return plan


def print_plan(plan: list[dict[str, Any]]) -> None:
    for entry in plan:
        print(f"\n[{entry['mode']}] {entry['started_at'].isoformat()}Z")
        for turn in entry["turns"]:
            print(f"  user: {turn['text']}")
            print(
                f"    -> emotion={turn['emotion']} confidence={turn['confidence']} "
                f"domains={turn['domains']} substances={turn['substances']} "
                f"sleep_hours={turn['sleep_hours']} wake_time={turn['wake_time']}"
            )
        print(f"  ai: {entry['ai_reply']}")
        print(f"  recap.title: {entry['recap']['title']}")


def seed(sb: Any, user_id: str, *, anchor: datetime) -> Manifest:
    plan = build_rows(user_id, anchor=anchor)
    manifest = Manifest(user_id=user_id, created_at=datetime.now(timezone.utc).isoformat())

    for entry in plan:
        session = (
            sb.table("chat_sessions")
            .insert(
                {
                    "user_id": user_id,
                    "checkin_mode": entry["mode"],
                    "status": "completed",
                    "started_at": entry["started_at"].isoformat(),
                    "ended_at": entry["ended_at"].isoformat(),
                    "preview": f"[seed] {entry['turns'][0]['text'][:50]}",
                }
            )
            .execute()
            .data[0]
        )
        session_id = session["id"]
        manifest.chat_session_ids.append(session_id)

        for turn in entry["turns"]:
            message = (
                sb.table("chat_messages")
                .insert(
                    {
                        "session_id": session_id,
                        "sender": "user",
                        "text": turn["text"],
                        "created_at": entry["started_at"].isoformat(),
                    }
                )
                .execute()
                .data[0]
            )
            message_id = message["id"]

            sb.table("message_analyses").insert(
                {
                    "message_id": message_id,
                    "session_id": session_id,
                    "emotion": turn["emotion"],
                    "emotion_scores": {turn["emotion"]: turn["confidence"]},
                    "domains": turn["domains"],
                    "sleep_substances": turn["substances"],
                    "sleep_hours": turn["sleep_hours"],
                    "wake_time": turn["wake_time"],
                    "confidence": turn["confidence"],
                    "source": turn["source"],
                    "risk_level": "none",
                    "model_id": "seed-script",
                    "model_revision": "n/a",
                    "created_at": entry["started_at"].isoformat(),
                }
            ).execute()

            for factor_key in _factor_keys_for(turn["domains"], turn["substances"]):
                existing = (
                    sb.table("sleep_factors")
                    .select("id")
                    .eq("user_id", user_id)
                    .eq("name_key", factor_key)
                    .execute()
                    .data
                )
                if existing:
                    factor_id = existing[0]["id"]
                else:
                    factor_id = (
                        sb.table("sleep_factors")
                        .insert({"user_id": user_id, "name_key": factor_key})
                        .execute()
                        .data[0]["id"]
                    )
                    manifest.sleep_factor_ids_created.append(factor_id)

                occurrence = (
                    sb.table("sleep_factor_occurrences")
                    .insert(
                        {
                            "factor_id": factor_id,
                            "session_id": session_id,
                            "message_id": message_id,
                            "checkin_label_key": _CHECKIN_LABEL[entry["mode"]],
                            "evidence_kind": "user_reported",
                            "source": turn["source"],
                            "confidence": turn["confidence"],
                            "occurred_at": entry["started_at"].isoformat(),
                        }
                    )
                    .execute()
                    .data[0]
                )
                manifest.sleep_factor_occurrence_ids.append(occurrence["id"])

        sb.table("chat_messages").insert(
            {
                "session_id": session_id,
                "sender": "ai",
                "text": entry["ai_reply"],
                "created_at": (entry["started_at"] + timedelta(seconds=5)).isoformat(),
            }
        ).execute()

        recap = entry["recap"]
        sb.table("session_recaps").insert(
            {
                "session_id": session_id,
                **recap,
                "generated_at": entry["ended_at"].isoformat(),
            }
        ).execute()

    return manifest


def cleanup(sb: Any, manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text())

    occurrence_ids = manifest.get("sleep_factor_occurrence_ids", [])
    if occurrence_ids:
        sb.table("sleep_factor_occurrences").delete().in_("id", occurrence_ids).execute()
        print(f"Deleted {len(occurrence_ids)} sleep_factor_occurrences rows.")

    session_ids = manifest.get("chat_session_ids", [])
    if session_ids:
        # Cascades to chat_messages, message_analyses, and session_recaps.
        sb.table("chat_sessions").delete().in_("id", session_ids).execute()
        print(f"Deleted {len(session_ids)} chat_sessions rows (cascaded messages/analyses/recaps).")

    for factor_id in manifest.get("sleep_factor_ids_created", []):
        remaining = (
            sb.table("sleep_factor_occurrences")
            .select("id", count="exact")
            .eq("factor_id", factor_id)
            .execute()
        )
        if (remaining.count or 0) == 0:
            sb.table("sleep_factors").delete().eq("id", factor_id).execute()
            print(f"Deleted now-empty sleep_factors row {factor_id}.")

    manifest_path.unlink()
    print(f"Removed manifest {manifest_path}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--email", help="Supabase auth user email to attach seeded rows to.")
    parser.add_argument("--user-id", help="Supabase auth user id to attach seeded rows to (skips email lookup).")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without writing anything.")
    parser.add_argument("--cleanup", metavar="MANIFEST_JSON", help="Delete everything recorded in a prior manifest.")
    args = parser.parse_args()

    sb = get_supabase()

    if args.cleanup:
        cleanup(sb, Path(args.cleanup))
        return

    user_id = resolve_user_id(sb, email=args.email, user_id=args.user_id)
    anchor = datetime.now(timezone.utc)
    plan = build_rows(user_id, anchor=anchor)

    if args.dry_run:
        print(f"Dry run for user_id={user_id} — nothing will be written.")
        print_plan(plan)
        return

    manifest = seed(sb, user_id, anchor=anchor)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = MANIFEST_DIR / f"{uuid.uuid4().hex}.json"
    manifest_path.write_text(json.dumps(manifest.to_json(), indent=2))

    print(f"Seeded {len(manifest.chat_session_ids)} sessions for user_id={user_id}.")
    print(f"Manifest written to {manifest_path}")
    print(f"To undo: python -m scripts.seed_stats_test_data --cleanup {manifest_path}")


if __name__ == "__main__":
    main()

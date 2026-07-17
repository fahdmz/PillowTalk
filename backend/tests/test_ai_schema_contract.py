from pathlib import Path

import pytest

SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "sql" / "ai_emotional_memory.sql"
)


@pytest.fixture(scope="module")
def schema_sql() -> str:
    return " ".join(SCHEMA_PATH.read_text(encoding="utf-8").lower().split())


@pytest.mark.parametrize(
    "table",
    ["message_analyses", "session_recaps", "safety_events"],
)
def test_creates_ai_tables_with_rls(schema_sql: str, table: str) -> None:
    assert f"create table if not exists public.{table}" in schema_sql
    assert f"alter table public.{table} enable row level security" in schema_sql


def test_uses_the_agreed_classifier_contract(schema_sql: str) -> None:
    for emotion in (
        "joy",
        "sadness",
        "anger",
        "fear",
        "surprise",
        "love",
        "neutral",
    ):
        assert f"'{emotion}'" in schema_sql

    for domain in (
        "relationship",
        "sleep",
        "work",
        "health",
        "sleep_substances",
    ):
        assert f"'{domain}'" in schema_sql

    for substance in (
        "caffeine",
        "alcohol",
        "nicotine",
        "sleep_medication",
        "other_stimulant",
        "other_sedative",
    ):
        assert f"'{substance}'" in schema_sql

    for field in ("sleep_hours", "wake_time", "confidence", "source"):
        assert field in schema_sql


def test_prevents_duplicate_active_sessions_and_recaps(schema_sql: str) -> None:
    assert "create unique index if not exists chat_sessions_one_active_per_mode_idx" in schema_sql
    assert "where status = 'active'" in schema_sql
    assert "session_id uuid not null unique" in schema_sql


def test_links_analysis_and_factor_evidence_to_source_messages(
    schema_sql: str,
) -> None:
    assert "message_id uuid not null unique" in schema_sql
    assert "add column if not exists message_id uuid" in schema_sql
    assert "evidence_kind" in schema_sql
    assert "user_reported" in schema_sql
    assert "system_inferred" in schema_sql


def test_ai_tables_only_allow_owned_authenticated_rows(schema_sql: str) -> None:
    assert schema_sql.count("to authenticated") >= 6
    assert schema_sql.count("(select auth.uid())") >= 6
    assert schema_sql.count("revoke all") >= 3
    assert schema_sql.count("grant select, delete") >= 3


def test_adds_indexes_for_memory_and_dashboard_queries(schema_sql: str) -> None:
    for index in (
        "message_analyses_session_created_idx",
        "session_recaps_generated_idx",
        "safety_events_session_created_idx",
        "sleep_factor_occurrences_message_idx",
    ):
        assert f"create index if not exists {index}" in schema_sql


def test_safety_events_do_not_duplicate_message_text(schema_sql: str) -> None:
    safety_table = schema_sql.split(
        "create table if not exists public.safety_events", maxsplit=1
    )[1].split("alter table public.safety_events", maxsplit=1)[0]
    assert "message_text" not in safety_table
    assert "transcript" not in safety_table

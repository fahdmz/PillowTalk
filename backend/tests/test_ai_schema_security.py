from pathlib import Path


def test_ai_sleep_factor_writes_are_backend_only() -> None:
    schema_path = (
        Path(__file__).resolve().parents[1] / "sql" / "ai_emotional_memory.sql"
    )
    sql = " ".join(schema_path.read_text(encoding="utf-8").lower().split())

    for table in ("sleep_factors", "sleep_factor_occurrences"):
        assert f"revoke all on table public.{table} from anon, authenticated" in sql
        assert f"grant select, delete on table public.{table} to authenticated" in sql

    assert "drop policy if exists \"sleep_factors_all_own\"" in sql
    assert "drop policy if exists \"sleep_factor_occurrences_all_own\"" in sql
    assert "sleep_factors_select_own" in sql
    assert "sleep_factor_occurrences_select_own" in sql

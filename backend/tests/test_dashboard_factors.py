from app.services.dashboard import build_factor_dashboard


def test_factor_dashboard_reconciles_source_rows_and_marks_small_samples():
    factors = [
        {"id": "factor-caffeine", "name_key": "caffeine"},
        {"id": "factor-work", "name_key": "work"},
    ]
    occurrences = [
        {
            "factor_id": "factor-caffeine",
            "checkin_label_key": "Nightly Check-in",
            "occurred_at": "2026-07-17T15:00:00+00:00",
            "evidence_kind": "user_reported",
            "source": "local",
            "confidence": 0.9,
        },
        {
            "factor_id": "factor-work",
            "checkin_label_key": "Morning Check-in",
            "occurred_at": "2026-07-17T01:00:00+00:00",
            "evidence_kind": "user_reported",
            "source": "local",
            "confidence": 0.8,
        },
        {
            "factor_id": "factor-work",
            "checkin_label_key": "Nightly Check-in",
            "occurred_at": "2026-07-16T15:00:00+00:00",
            "evidence_kind": "user_reported",
            "source": "foundry_fallback",
            "confidence": 0.6,
        },
        {
            "factor_id": "factor-work",
            "checkin_label_key": "Nightly Check-in",
            "occurred_at": "2026-07-15T15:00:00+00:00",
            "evidence_kind": "user_reported",
            "source": "local",
            "confidence": 0.7,
        },
    ]

    rows = build_factor_dashboard(factors, occurrences, minimum_samples=2)

    assert sum(row["sample_size"] for row in rows) == len(occurrences)
    assert rows[0]["name_key"] == "work"
    assert rows[0]["sample_size"] == 3
    assert rows[0]["level"] == "high"
    assert rows[0]["trend_status"] == "observed"
    assert rows[0]["mean_confidence"] == 0.7
    assert rows[1]["name_key"] == "caffeine"
    assert rows[1]["level"] == "low"
    assert rows[1]["trend_status"] == "insufficient_data"
    assert rows[1]["sample_size"] == 1

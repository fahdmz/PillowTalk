from datetime import datetime, timezone

from app.services.dashboard import build_weekly_sleep_dashboard


def test_weekly_sleep_uses_latest_report_per_local_day_and_reconciles_samples():
    analyses = [
        {
            "sleep_hours": 6.0,
            "wake_time": "06:00",
            "created_at": "2026-07-16T17:30:00+00:00",
        },
        {
            "sleep_hours": 7.0,
            "wake_time": "06:30",
            "created_at": "2026-07-16T18:00:00+00:00",
        },
        {
            "sleep_hours": 8.0,
            "wake_time": "07:30",
            "created_at": "2026-07-17T18:00:00+00:00",
        },
        {
            "sleep_hours": None,
            "wake_time": None,
            "created_at": "2026-07-17T19:00:00+00:00",
        },
    ]

    result = build_weekly_sleep_dashboard(
        analyses,
        now=datetime(2026, 7, 18, 2, 0, tzinfo=timezone.utc),
        timezone_offset_minutes=420,
        minimum_samples=2,
    )

    assert result["week"] == [
        {"day": "Fri", "hours": 7.0},
        {"day": "Sat", "hours": 8.0},
    ]
    assert result["sample_size"] == 2
    assert result["trend_status"] == "observed"
    assert result["avg_sleep_hours"] == 7.5
    assert result["avg_sleep_time"] == "23:30"
    assert result["avg_wake_time"] == "07:00"

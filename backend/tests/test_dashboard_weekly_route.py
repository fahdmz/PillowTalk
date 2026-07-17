from datetime import datetime, timezone

from app.routers import profile


class FakeDashboardRepository:
    calls = []

    def __init__(self, supabase):
        self.supabase = supabase

    def load_sleep_analyses(self, **kwargs):
        self.calls.append(kwargs)
        return [
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
        ]


def test_weekly_route_reads_normalized_analyses_with_local_boundary(monkeypatch):
    FakeDashboardRepository.calls = []
    monkeypatch.setattr(profile, "get_supabase", lambda: object())
    monkeypatch.setattr(profile, "SupabaseDashboardRepository", FakeDashboardRepository)
    monkeypatch.setattr(
        profile,
        "_now_utc",
        lambda: datetime(2026, 7, 18, 2, 0, tzinfo=timezone.utc),
    )

    result = profile.get_weekly_sleep(
        days=7,
        timezone_offset_minutes=420,
        user_id="user-1",
    )

    assert FakeDashboardRepository.calls[0]["user_id"] == "user-1"
    assert FakeDashboardRepository.calls[0]["since"].isoformat() == (
        "2026-07-11T17:00:00+00:00"
    )
    assert result.sample_size == 2
    assert result.avg_sleep_hours == 7.5
    assert result.avg_sleep_time == "23:30"
    assert result.avg_wake_time == "07:00"

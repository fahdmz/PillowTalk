from datetime import datetime, timezone

from app.routers import profile


class FakeDashboardRepository:
    calls = []

    def __init__(self, supabase):
        self.supabase = supabase

    def load_sleep_factors(self, **kwargs):
        self.calls.append(kwargs)
        return [{
            "name_key": "caffeine",
            "level": "low",
            "trend_status": "insufficient_data",
            "sample_size": 1,
            "mean_confidence": 0.9,
            "interpretation": "observed_alongside_checkins",
            "occurrences": [{
                "checkin_label_key": "Nightly Check-in",
                "occurred_at": "2026-07-17T15:00:00+00:00",
                "evidence_kind": "user_reported",
                "source": "local",
                "confidence": 0.9,
            }],
        }]


def test_sleep_factor_route_uses_local_day_window_and_returns_uncertainty(monkeypatch):
    FakeDashboardRepository.calls = []
    monkeypatch.setattr(profile, "get_supabase", lambda: object())
    monkeypatch.setattr(profile, "SupabaseDashboardRepository", FakeDashboardRepository)
    monkeypatch.setattr(
        profile,
        "_now_utc",
        lambda: datetime(2026, 7, 17, 20, 0, tzinfo=timezone.utc),
    )

    rows = profile.get_sleep_factors(
        days=30,
        timezone_offset_minutes=420,
        user_id="user-1",
    )

    assert FakeDashboardRepository.calls[0]["user_id"] == "user-1"
    assert FakeDashboardRepository.calls[0]["since"].isoformat() == (
        "2026-06-18T17:00:00+00:00"
    )
    assert rows[0].name_key == "caffeine"
    assert rows[0].sample_size == 1
    assert rows[0].trend_status == "insufficient_data"
    assert rows[0].occurrences[0].evidence_kind == "user_reported"

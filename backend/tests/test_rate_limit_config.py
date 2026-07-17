import pytest

from app.config import Settings


def test_rate_limit_settings_are_parsed(monkeypatch):
    monkeypatch.setenv("CHAT_RATE_LIMIT_REQUESTS", "15")
    monkeypatch.setenv("CHAT_RATE_LIMIT_WINDOW_SECONDS", "45")

    settings = Settings()

    assert settings.chat_rate_limit_requests == 15
    assert settings.chat_rate_limit_window_seconds == 45


@pytest.mark.parametrize(
    "name", ["CHAT_RATE_LIMIT_REQUESTS", "CHAT_RATE_LIMIT_WINDOW_SECONDS"]
)
def test_rate_limit_settings_must_be_positive(monkeypatch, name):
    monkeypatch.setenv(name, "0")

    with pytest.raises(RuntimeError, match=name):
        Settings()

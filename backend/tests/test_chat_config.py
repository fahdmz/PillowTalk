import pytest

from app.config import Settings


def test_chat_memory_and_safety_settings_are_parsed(monkeypatch):
    monkeypatch.setenv("CHAT_RECENT_MESSAGE_LIMIT", "10")
    monkeypatch.setenv("CHAT_MEMORY_SESSION_LIMIT", "2")
    monkeypatch.setenv("CHAT_MEMORY_LOOKBACK_DAYS", "7")
    monkeypatch.setenv("CHAT_MAX_OUTPUT_TOKENS", "600")
    monkeypatch.setenv("CRISIS_RESOURCE_NAME", "Healing119")
    monkeypatch.setenv("CRISIS_RESOURCE_PHONE", "119 ext. 8")
    monkeypatch.setenv("CRISIS_RESOURCE_URL", "https://www.healing119.id")

    settings = Settings()

    assert settings.chat_recent_message_limit == 10
    assert settings.chat_memory_session_limit == 2
    assert settings.chat_memory_lookback_days == 7
    assert settings.chat_max_output_tokens == 600
    assert settings.crisis_resource_name == "Healing119"


def test_validate_chat_requires_chat_deployment(monkeypatch):
    monkeypatch.setenv("AZURE_AI_FOUNDRY_ENDPOINT", "https://resource.services.ai.azure.com")
    monkeypatch.setenv("AZURE_AI_FOUNDRY_API_KEY", "key")
    monkeypatch.delenv("AZURE_AI_FOUNDRY_CHAT_DEPLOYMENT", raising=False)

    with pytest.raises(RuntimeError, match="AZURE_AI_FOUNDRY_CHAT_DEPLOYMENT"):
        Settings().validate_chat()


@pytest.mark.parametrize("name", [
    "CHAT_RECENT_MESSAGE_LIMIT",
    "CHAT_MEMORY_SESSION_LIMIT",
    "CHAT_MEMORY_LOOKBACK_DAYS",
    "CHAT_MAX_OUTPUT_TOKENS",
])
def test_invalid_chat_limits_fail_fast(monkeypatch, name):
    monkeypatch.setenv(name, "0")

    with pytest.raises(RuntimeError, match=name):
        Settings()

import pytest

from app.config import Settings


def set_ai_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "AZURE_AI_FOUNDRY_ENDPOINT", "https://resource.services.ai.azure.com/"
    )
    monkeypatch.setenv("AZURE_AI_FOUNDRY_API_KEY", "foundry-key")
    monkeypatch.setenv("AZURE_AI_FOUNDRY_CLASSIFIER_DEPLOYMENT", "classifier")


def test_ai_settings_are_parsed_without_affecting_supabase_validation(monkeypatch):
    set_ai_environment(monkeypatch)
    monkeypatch.setenv("EMOTION_LOCAL_CONFIDENCE_THRESHOLD", "0.72")
    monkeypatch.setenv("EMOTION_FALLBACK_ENABLED", "false")

    settings = Settings()

    assert settings.azure_ai_foundry_endpoint == (
        "https://resource.services.ai.azure.com"
    )
    assert settings.emotion_local_confidence_threshold == 0.72
    assert settings.emotion_fallback_enabled is False


def test_validate_ai_requires_foundry_values_only_when_fallback_is_enabled(monkeypatch):
    monkeypatch.setenv("EMOTION_FALLBACK_ENABLED", "false")
    monkeypatch.delenv("AZURE_AI_FOUNDRY_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_AI_FOUNDRY_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_AI_FOUNDRY_CLASSIFIER_DEPLOYMENT", raising=False)

    Settings().validate_ai()

    monkeypatch.setenv("EMOTION_FALLBACK_ENABLED", "true")
    with pytest.raises(RuntimeError, match="AZURE_AI_FOUNDRY_ENDPOINT"):
        Settings().validate_ai()


@pytest.mark.parametrize("value", ["-0.1", "1.1", "unknown"])
def test_invalid_local_confidence_threshold_fails_fast(monkeypatch, value):
    monkeypatch.setenv("EMOTION_LOCAL_CONFIDENCE_THRESHOLD", value)

    with pytest.raises(RuntimeError):
        Settings()


def test_invalid_boolean_fails_fast(monkeypatch):
    monkeypatch.setenv("EMOTION_FALLBACK_ENABLED", "sometimes")

    with pytest.raises(RuntimeError, match="EMOTION_FALLBACK_ENABLED"):
        Settings()


from app.config import Settings


def test_recap_settings_use_dedicated_deployment_or_classifier_fallback(monkeypatch):
    monkeypatch.setenv("AZURE_AI_FOUNDRY_CLASSIFIER_DEPLOYMENT", "gpt-mini")
    monkeypatch.delenv("AZURE_AI_FOUNDRY_RECAP_DEPLOYMENT", raising=False)
    monkeypatch.setenv("RECAP_MAX_OUTPUT_TOKENS", "500")
    monkeypatch.setenv("RECAP_GENERATION_INPUT_LIMIT", "200")

    fallback = Settings()
    assert fallback.azure_ai_foundry_recap_deployment == "gpt-mini"
    assert fallback.recap_max_output_tokens == 500
    assert fallback.recap_generation_input_limit == 200

    monkeypatch.setenv("AZURE_AI_FOUNDRY_RECAP_DEPLOYMENT", "gpt-recap")
    assert Settings().azure_ai_foundry_recap_deployment == "gpt-recap"

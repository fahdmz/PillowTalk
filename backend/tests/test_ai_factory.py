from app.services import ai_factory


class FakeSettings:
    emotion_model_id = "local/model"
    emotion_model_revision = "revision"
    emotion_local_confidence_threshold = 0.7
    emotion_model_device = "cpu"
    hf_token = None
    emotion_fallback_enabled = True
    azure_ai_foundry_endpoint = "https://resource.services.ai.azure.com"
    azure_ai_foundry_api_key = "key"
    azure_ai_foundry_timeout_seconds = 20
    azure_ai_foundry_max_retries = 2
    azure_ai_foundry_classifier_deployment = "classifier"

    def __init__(self):
        self.validated = False

    def validate_ai(self):
        self.validated = True


def test_factory_wires_local_and_foundry_without_loading_the_local_model(monkeypatch):
    fake_settings = FakeSettings()
    created_clients = []
    monkeypatch.setattr(ai_factory, "settings", fake_settings)
    monkeypatch.setattr(
        ai_factory,
        "create_async_foundry_client",
        lambda **kwargs: created_clients.append(kwargs) or object(),
    )
    ai_factory.get_message_analyzer.cache_clear()

    analyzer = ai_factory.get_message_analyzer()

    assert fake_settings.validated is True
    assert analyzer.local_classifier._pipeline is None
    assert analyzer.local_classifier.model_id == "local/model"
    assert analyzer.fallback_classifier.deployment == "classifier"
    assert created_clients[0]["endpoint"].endswith("services.ai.azure.com")
    ai_factory.get_message_analyzer.cache_clear()

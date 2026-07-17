from app.services import recap_factory


class FakeSettings:
    azure_ai_foundry_endpoint = "https://resource.services.ai.azure.com"
    azure_ai_foundry_api_key = "key"
    azure_ai_foundry_timeout_seconds = 30
    azure_ai_foundry_max_retries = 2
    azure_ai_foundry_recap_deployment = "gpt-recap"
    recap_max_output_tokens = 500
    recap_generation_input_limit = 200

    def __init__(self):
        self.validated = []

    def validate(self):
        self.validated.append("database")

    def validate_recap(self):
        self.validated.append("recap")


def test_recap_factory_wires_supabase_and_foundry_without_calling_either(monkeypatch):
    settings = FakeSettings()
    supabase = object()
    client = object()
    monkeypatch.setattr(recap_factory, "settings", settings)
    monkeypatch.setattr(recap_factory, "get_supabase", lambda: supabase)
    monkeypatch.setattr(
        recap_factory, "create_async_foundry_client", lambda **kwargs: client
    )
    recap_factory.get_recap_service.cache_clear()

    service = recap_factory.get_recap_service()

    assert settings.validated == ["database", "recap"]
    assert service.repository.supabase is supabase
    assert service.repository.generation_input_limit == 200
    assert service.generator.client is client
    assert service.generator.deployment == "gpt-recap"
    assert service.generator.max_output_tokens == 500
    recap_factory.get_recap_service.cache_clear()

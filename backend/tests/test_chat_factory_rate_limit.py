from app.services import chat_factory


class FakeSettings:
    chat_recent_message_limit = 12
    chat_memory_session_limit = 3
    chat_memory_lookback_days = 14
    chat_max_output_tokens = 800
    chat_rate_limit_requests = 9
    chat_rate_limit_window_seconds = 30
    azure_ai_foundry_endpoint = "https://resource.services.ai.azure.com"
    azure_ai_foundry_api_key = "key"
    azure_ai_foundry_timeout_seconds = 30
    azure_ai_foundry_max_retries = 2
    azure_ai_foundry_chat_deployment = "chat"
    crisis_resource_name = "Healing119"
    crisis_resource_phone = "119 ext. 8"
    crisis_resource_url = "https://www.healing119.id"

    def validate(self): pass
    def validate_ai(self): pass
    def validate_chat(self): pass


def test_chat_factory_configures_per_user_rate_limiter(monkeypatch):
    monkeypatch.setattr(chat_factory, "settings", FakeSettings())
    monkeypatch.setattr(chat_factory, "get_supabase", lambda: object())
    monkeypatch.setattr(chat_factory, "get_message_analyzer", lambda: object())
    monkeypatch.setattr(
        chat_factory, "create_async_foundry_client", lambda **kwargs: object()
    )
    chat_factory.get_chat_orchestrator.cache_clear()

    orchestrator = chat_factory.get_chat_orchestrator()

    assert orchestrator.rate_limiter.max_requests == 9
    assert orchestrator.rate_limiter.window_seconds == 30
    chat_factory.get_chat_orchestrator.cache_clear()

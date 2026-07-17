from app.services import chat_factory


class FakeSettings:
    chat_recent_message_limit = 12
    chat_memory_session_limit = 3
    chat_memory_lookback_days = 14
    chat_max_output_tokens = 800
    chat_rate_limit_requests = 20
    chat_rate_limit_window_seconds = 60
    azure_ai_foundry_endpoint = "https://resource.services.ai.azure.com"
    azure_ai_foundry_api_key = "key"
    azure_ai_foundry_timeout_seconds = 30
    azure_ai_foundry_max_retries = 2
    azure_ai_foundry_chat_deployment = "chat"
    crisis_resource_name = "Healing119"
    crisis_resource_phone = "119 ext. 8"
    crisis_resource_url = "https://www.healing119.id"

    def __init__(self):
        self.validated = []

    def validate(self):
        self.validated.append("database")

    def validate_ai(self):
        self.validated.append("ai")

    def validate_chat(self):
        self.validated.append("chat")


def test_chat_factory_wires_repository_analyzer_safety_and_foundry(monkeypatch):
    settings = FakeSettings()
    analyzer = object()
    supabase = object()
    client = object()
    monkeypatch.setattr(chat_factory, "settings", settings)
    monkeypatch.setattr(chat_factory, "get_supabase", lambda: supabase)
    monkeypatch.setattr(chat_factory, "get_message_analyzer", lambda: analyzer)
    monkeypatch.setattr(
        chat_factory, "create_async_foundry_client", lambda **kwargs: client
    )
    chat_factory.get_chat_orchestrator.cache_clear()

    orchestrator = chat_factory.get_chat_orchestrator()

    assert settings.validated == ["database", "ai", "chat"]
    assert orchestrator.repository.supabase is supabase
    assert orchestrator.analyzer is analyzer
    assert orchestrator.chatbot.client is client
    assert orchestrator.chatbot.deployment == "chat"
    chat_factory.get_chat_orchestrator.cache_clear()

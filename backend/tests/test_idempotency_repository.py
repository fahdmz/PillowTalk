from types import SimpleNamespace

from app.services.idempotent_chat_repository import IdempotentSupabaseChatRepository


class Query:
    def __init__(self, client):
        self.client = client; self.operation = None; self.payload = None; self.filters = []
    def select(self, columns): self.operation = "select"; return self
    def insert(self, payload): self.operation = "insert"; self.payload = payload; return self
    def eq(self, column, value): self.filters.append((column, value)); return self
    def limit(self, value): return self
    def execute(self):
        self.client.calls.append(self)
        queue = self.client.responses.get(self.operation, [])
        return SimpleNamespace(data=queue.pop(0) if queue else [])


class Supabase:
    def __init__(self, responses): self.responses = responses; self.calls = []
    def table(self, name): return Query(self)


def test_repository_loads_user_message_and_linked_ai_reply():
    sb = Supabase({"select": [
        [{"id": "user-message", "sender": "user", "text": "Halo"}],
        [{"id": "ai-message", "sender": "ai", "text": "Hai"}],
    ]})
    turn = IdempotentSupabaseChatRepository(sb).find_idempotent_turn("session-1", "request-123")
    assert turn["ai_message"]["id"] == "ai-message"
    assert ("reply_to_message_id", "user-message") in sb.calls[1].filters


def test_repository_reserves_key_and_links_reply():
    sb = Supabase({"insert": [
        [{"id": "user-message", "sender": "user", "text": "Halo"}],
        [{"id": "ai-message", "sender": "ai", "text": "Hai"}],
    ]})
    repository = IdempotentSupabaseChatRepository(sb)
    repository.reserve_idempotency_key("session-1", "request-123", text="Halo")
    repository.insert_reply("session-1", "user-message", "Hai")
    assert sb.calls[0].payload["idempotency_key"] == "request-123"
    assert sb.calls[1].payload["reply_to_message_id"] == "user-message"

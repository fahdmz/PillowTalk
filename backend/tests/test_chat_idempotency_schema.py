from pathlib import Path


SQL = Path(__file__).parents[1] / "sql" / "chat_idempotency.sql"


def test_idempotency_query_adds_request_key_and_reply_linkage_constraints():
    sql = SQL.read_text(encoding="utf-8").casefold()

    assert "add column if not exists idempotency_key text" in sql
    assert "add column if not exists reply_to_message_id uuid" in sql
    assert "chat_messages_user_idempotency_uidx" in sql
    assert "chat_messages_ai_reply_uidx" in sql
    assert "foreign key (reply_to_message_id, session_id)" in sql
    assert "where sender = 'user'" in sql
    assert "where sender = 'ai'" in sql
    assert "begin;" in sql and "commit;" in sql

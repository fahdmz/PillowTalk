from pathlib import Path


SQL = Path(__file__).parents[1] / "sql" / "chat_idempotency.sql"


def test_query_uses_plain_postgres_statements_without_dollar_quoted_do_block():
    sql = SQL.read_text(encoding="utf-8").casefold()

    assert "do $$" not in sql
    assert "drop constraint if exists chat_messages_reply_to_message_fkey" in sql
    assert "drop constraint if exists chat_messages_idempotency_sender_check" in sql
    assert "drop constraint if exists chat_messages_reply_sender_check" in sql

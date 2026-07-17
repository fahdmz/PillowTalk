"""Durable chat-turn idempotency coordination."""

from typing import Any

from fastapi import HTTPException


class IdempotencyPending(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409,
            detail="A request with this Idempotency-Key is still processing",
            headers={"Retry-After": "2"},
        )


def replay_or_reserve(
    repository: Any,
    session_id: str,
    idempotency_key: str,
) -> dict[str, Any]:
    existing = repository.find_idempotent_turn(session_id, idempotency_key)
    if existing is not None:
        if existing.get("ai_message") is None:
            raise IdempotencyPending()
        return existing
    user_message = repository.reserve_idempotency_key(session_id, idempotency_key)
    return {"user_message": user_message, "ai_message": None}

import pytest

from app.services.idempotency import IdempotencyPending, replay_or_reserve


class Repository:
    def __init__(self, turn):
        self.turn = turn
        self.reservations = []

    def find_idempotent_turn(self, session_id, key):
        return self.turn

    def reserve_idempotency_key(self, session_id, key):
        self.reservations.append((session_id, key))
        return {"id": "user-message", "sender": "user", "text": "Halo"}


def test_completed_turn_is_replayed_without_reservation():
    completed = {
        "user_message": {"id": "user-message", "sender": "user", "text": "Halo"},
        "ai_message": {"id": "ai-message", "sender": "ai", "text": "Hai"},
    }
    repository = Repository(completed)

    result = replay_or_reserve(repository, "session-1", "request-123")

    assert result == completed
    assert repository.reservations == []


def test_pending_turn_returns_retryable_conflict():
    repository = Repository(
        {
            "user_message": {"id": "user-message", "sender": "user", "text": "Halo"},
            "ai_message": None,
        }
    )

    with pytest.raises(IdempotencyPending) as raised:
        replay_or_reserve(repository, "session-1", "request-123")

    assert raised.value.status_code == 409
    assert raised.value.headers == {"Retry-After": "2"}


def test_new_key_is_reserved_once():
    repository = Repository(None)

    result = replay_or_reserve(repository, "session-1", "request-123")

    assert result["user_message"]["id"] == "user-message"
    assert result["ai_message"] is None
    assert repository.reservations == [("session-1", "request-123")]

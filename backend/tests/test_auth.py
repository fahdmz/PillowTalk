from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jwt.exceptions import PyJWKClientConnectionError

from app import deps

ISSUER = "https://project-ref.supabase.co/auth/v1"


@pytest.fixture
def rsa_keys() -> tuple[Any, Any]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def _claims(**overrides: Any) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    claims: dict[str, Any] = {
        "aud": "authenticated",
        "exp": now + timedelta(minutes=5),
        "iat": now,
        "iss": ISSUER,
        "sub": "user-123",
    }
    claims.update(overrides)
    return claims


def _token(private_key: Any, **claim_overrides: Any) -> str:
    return jwt.encode(
        _claims(**claim_overrides),
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


def _install_key(monkeypatch: pytest.MonkeyPatch, public_key: Any) -> None:
    client = SimpleNamespace(
        get_signing_key_from_jwt=lambda _token: SimpleNamespace(key=public_key)
    )
    monkeypatch.setattr(deps, "get_jwk_client", lambda: client)
    monkeypatch.setattr(deps.settings, "supabase_url", "https://project-ref.supabase.co")


def test_valid_asymmetric_token_returns_claims(
    monkeypatch: pytest.MonkeyPatch,
    rsa_keys: tuple[Any, Any],
) -> None:
    private_key, public_key = rsa_keys
    _install_key(monkeypatch, public_key)

    claims = deps.get_current_user_claims(f"Bearer {_token(private_key)}")

    assert claims["sub"] == "user-123"


@pytest.mark.parametrize(
    ("overrides", "expected_status"),
    [
        ({"aud": "wrong-audience"}, 401),
        ({"iss": "https://other-project.supabase.co/auth/v1"}, 401),
        ({"exp": datetime.now(timezone.utc) - timedelta(seconds=1)}, 401),
        ({"sub": None}, 401),
    ],
)
def test_invalid_claims_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    rsa_keys: tuple[Any, Any],
    overrides: dict[str, Any],
    expected_status: int,
) -> None:
    private_key, public_key = rsa_keys
    _install_key(monkeypatch, public_key)

    with pytest.raises(HTTPException) as error:
        deps.get_current_user_claims(f"Bearer {_token(private_key, **overrides)}")

    assert error.value.status_code == expected_status
    assert error.value.detail == "Invalid or expired token"


def test_hs256_token_is_rejected_before_key_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        deps,
        "get_jwk_client",
        lambda: pytest.fail("JWKS lookup must not run for HS256"),
    )
    token = jwt.encode(_claims(), "legacy-secret", algorithm="HS256")

    with pytest.raises(HTTPException) as error:
        deps.get_current_user_claims(f"Bearer {token}")

    assert error.value.status_code == 401
    assert error.value.detail == "Unsupported token signing algorithm"


def test_jwks_connection_failure_returns_retryable_error(
    monkeypatch: pytest.MonkeyPatch,
    rsa_keys: tuple[Any, Any],
) -> None:
    private_key, _public_key = rsa_keys

    def unavailable(_token: str) -> None:
        raise PyJWKClientConnectionError("offline")

    monkeypatch.setattr(
        deps,
        "get_jwk_client",
        lambda: SimpleNamespace(get_signing_key_from_jwt=unavailable),
    )

    with pytest.raises(HTTPException) as error:
        deps.get_current_user_claims(f"Bearer {_token(private_key)}")

    assert error.value.status_code == 503
    assert error.value.headers == {"Retry-After": "5"}

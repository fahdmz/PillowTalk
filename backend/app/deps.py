from functools import lru_cache
from typing import Any, Optional

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWTError

from .config import settings

_ALLOWED_SIGNING_ALGORITHMS = frozenset({"ES256", "RS256"})


@lru_cache(maxsize=4)
def _create_jwk_client(
    jwks_url: str,
    cache_seconds: int,
    timeout_seconds: int,
) -> PyJWKClient:
    # Cache only the JWKS document. PyJWKClient refreshes it when a token has
    # an unknown kid, which supports zero-downtime Supabase key rotation.
    return PyJWKClient(
        jwks_url,
        cache_keys=False,
        cache_jwk_set=True,
        lifespan=cache_seconds,
        timeout=timeout_seconds,
    )


def get_jwk_client() -> PyJWKClient:
    return _create_jwk_client(
        settings.supabase_jwks_url,
        settings.supabase_jwks_cache_seconds,
        settings.supabase_jwks_timeout_seconds,
    )


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_claims(
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Verify a Supabase access token against the project's public JWKS."""
    if not authorization:
        raise _unauthorized("Missing bearer token")

    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise _unauthorized("Missing bearer token")
    token = token.strip()

    try:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")
        if algorithm not in _ALLOWED_SIGNING_ALGORITHMS:
            raise _unauthorized("Unsupported token signing algorithm")

        signing_key = get_jwk_client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            audience="authenticated",
            issuer=settings.supabase_auth_issuer,
            options={"require": ["aud", "exp", "iss", "sub"]},
        )
    except HTTPException:
        raise
    except PyJWKClientConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication key service unavailable",
            headers={"Retry-After": "5"},
        ) from exc
    except PyJWTError as exc:
        raise _unauthorized("Invalid or expired token") from exc


def get_current_user_id(
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> str:
    return str(claims["sub"])

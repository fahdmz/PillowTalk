from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status

from .config import settings


def get_current_user_claims(authorization: Optional[str] = Header(default=None)) -> dict:
    """Verifies the Supabase-issued JWT the Flutter app sends on every
    request (it gets this token from supabase_flutter after login/signup —
    this backend never issues or checks passwords itself). Returns the full
    claim set, since `user_metadata` (e.g. full_name from signup) lives here
    too and some routes want it.

    The header is declared optional here (rather than `Header(...)`) so a
    missing header reaches this function and comes back as a clean 401 —
    otherwise FastAPI's own request validation rejects it with a 422 before
    our code ever runs."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
        ) from exc

    if not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )
    return payload


def get_current_user_id(claims: dict = Depends(get_current_user_claims)) -> str:
    return claims["sub"]

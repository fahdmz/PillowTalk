from functools import lru_cache

from supabase import Client, create_client

from .config import settings


@lru_cache
def get_supabase() -> Client:
    """Service-role Supabase client. This bypasses row-level security, so
    every query in this codebase MUST be scoped by the caller's user_id
    (taken from the verified JWT in app/deps.py) — RLS in schema.sql is the
    backstop for direct/anon client access, not a substitute for that."""
    settings.validate()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)

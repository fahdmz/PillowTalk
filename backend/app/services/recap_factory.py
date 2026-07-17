"""FastAPI dependency factory for completed-session recap generation."""

from functools import lru_cache
from typing import Any

from app.config import settings
from app.services.foundry_client import create_async_foundry_client
from app.services.recap_generator import FoundryRecapGenerator
from app.services.recap_repository import SupabaseRecapRepository
from app.services.recap_service import RecapService


def get_supabase() -> Any:
    from app.database import get_supabase as get_database_client

    return get_database_client()


@lru_cache(maxsize=1)
def get_recap_service() -> RecapService:
    settings.validate()
    settings.validate_recap()
    client = create_async_foundry_client(
        endpoint=settings.azure_ai_foundry_endpoint,
        api_key=settings.azure_ai_foundry_api_key,
        timeout_seconds=settings.azure_ai_foundry_timeout_seconds,
        max_retries=settings.azure_ai_foundry_max_retries,
    )
    return RecapService(
        repository=SupabaseRecapRepository(
            get_supabase(),
            generation_input_limit=settings.recap_generation_input_limit,
        ),
        generator=FoundryRecapGenerator(
            client=client,
            deployment=settings.azure_ai_foundry_recap_deployment,
            max_output_tokens=settings.recap_max_output_tokens,
        ),
    )

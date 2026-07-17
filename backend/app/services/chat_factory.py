"""FastAPI dependency factory for the complete protected chat workflow."""

from functools import lru_cache
from typing import Annotated, Any

from fastapi import Header, HTTPException

from app.config import settings
from app.services.ai_factory import get_message_analyzer
from app.services.chat_orchestrator import ChatOrchestrator
from app.services.foundry_chatbot import FoundryChatbot
from app.services.foundry_client import create_async_foundry_client
from app.services.idempotent_chat_repository import IdempotentSupabaseChatRepository
from app.services.idempotent_orchestrator import IdempotentChatOrchestrator
from app.services.rate_limiter import InMemoryRateLimiter
from app.services.recap_factory import get_recap_service
from app.services.safety import SafetyScreen


def get_supabase() -> Any:
    from app.database import get_supabase as get_database_client
    return get_database_client()


@lru_cache(maxsize=1)
def _get_base_orchestrator() -> IdempotentChatOrchestrator:
    settings.validate(); settings.validate_ai(); settings.validate_chat()
    repository = IdempotentSupabaseChatRepository(
        get_supabase(), message_limit=settings.chat_recent_message_limit,
        recap_limit=settings.chat_memory_session_limit,
        lookback_days=settings.chat_memory_lookback_days,
    )
    client = create_async_foundry_client(
        endpoint=settings.azure_ai_foundry_endpoint,
        api_key=settings.azure_ai_foundry_api_key,
        timeout_seconds=settings.azure_ai_foundry_timeout_seconds,
        max_retries=settings.azure_ai_foundry_max_retries,
    )
    inner = ChatOrchestrator(
        repository=repository, safety_screen=SafetyScreen(),
        analyzer=get_message_analyzer(),
        chatbot=FoundryChatbot(
            client=client, deployment=settings.azure_ai_foundry_chat_deployment,
            max_output_tokens=settings.chat_max_output_tokens,
        ),
        rate_limiter=InMemoryRateLimiter(
            max_requests=settings.chat_rate_limit_requests,
            window_seconds=settings.chat_rate_limit_window_seconds,
        ),
        resource_name=settings.crisis_resource_name,
        resource_phone=settings.crisis_resource_phone,
        resource_url=settings.crisis_resource_url,
        recap_service=get_recap_service(),
        max_user_turns=settings.chat_max_user_turns,
    )
    return IdempotentChatOrchestrator(inner)


class _RequestBoundOrchestrator:
    def __init__(self, orchestrator: IdempotentChatOrchestrator, key: str | None) -> None:
        self.orchestrator = orchestrator; self.key = key

    def __getattr__(self, name: str) -> Any:
        return getattr(self.orchestrator.inner, name)

    async def send_message(self, **kwargs: Any):
        return await self.orchestrator.send_message(idempotency_key=self.key, **kwargs)


def get_chat_orchestrator(
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> _RequestBoundOrchestrator:
    if idempotency_key is not None and not 8 <= len(idempotency_key) <= 128:
        raise HTTPException(status_code=400, detail="Idempotency-Key must contain 8 to 128 characters")
    return _RequestBoundOrchestrator(_get_base_orchestrator(), idempotency_key)


get_chat_orchestrator.cache_clear = _get_base_orchestrator.cache_clear

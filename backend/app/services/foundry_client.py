"""Azure AI Foundry client construction helpers."""

from typing import Any


def build_foundry_base_url(endpoint: str) -> str:
    """Return an Azure OpenAI v1-compatible base URL for a Foundry endpoint."""
    normalized_endpoint = endpoint.strip().rstrip("/")
    if normalized_endpoint.endswith("/openai/v1"):
        return f"{normalized_endpoint}/"
    return f"{normalized_endpoint}/openai/v1/"


def create_async_foundry_client(
    *,
    endpoint: str,
    api_key: str,
    timeout_seconds: float,
    max_retries: int,
) -> Any:
    """Create an async OpenAI-compatible client without importing it at startup."""
    try:
        from openai import AsyncOpenAI
    except ImportError as exc:  # pragma: no cover - depends on deployment extras
        raise RuntimeError(
            "The OpenAI SDK is required for Azure AI Foundry. "
            "Install the backend requirements before starting the API."
        ) from exc

    return AsyncOpenAI(
        api_key=api_key,
        base_url=build_foundry_base_url(endpoint),
        timeout=timeout_seconds,
        max_retries=max_retries,
    )

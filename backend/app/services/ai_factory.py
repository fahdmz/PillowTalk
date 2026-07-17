"""Construct the configured message-analysis service graph."""

from functools import lru_cache

from app.config import settings
from app.services.analysis_service import MessageAnalyzer
from app.services.classifier import LocalEmotionClassifier
from app.services.fallback_classifier import FoundryFallbackClassifier
from app.services.foundry_client import create_async_foundry_client


@lru_cache(maxsize=1)
def get_message_analyzer() -> MessageAnalyzer:
    """Build once; heavyweight local model loading remains lazy until first use."""
    settings.validate_ai()
    local_classifier = LocalEmotionClassifier(
        model_id=settings.emotion_model_id,
        revision=settings.emotion_model_revision,
        confidence_threshold=settings.emotion_local_confidence_threshold,
        device=settings.emotion_model_device,
        hf_token=settings.hf_token,
    )

    fallback_classifier = None
    if settings.emotion_fallback_enabled:
        client = create_async_foundry_client(
            endpoint=settings.azure_ai_foundry_endpoint,
            api_key=settings.azure_ai_foundry_api_key,
            timeout_seconds=settings.azure_ai_foundry_timeout_seconds,
            max_retries=settings.azure_ai_foundry_max_retries,
        )
        fallback_classifier = FoundryFallbackClassifier(
            client=client,
            deployment=settings.azure_ai_foundry_classifier_deployment,
        )

    return MessageAnalyzer(
        local_classifier=local_classifier,
        fallback_classifier=fallback_classifier,
        fallback_enabled=settings.emotion_fallback_enabled,
    )

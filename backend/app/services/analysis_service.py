"""Local-first message analysis orchestration."""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.analysis import AnalysisResult, AnalysisSource, Emotion, RiskLevel
from app.services.analysis_normalizer import extract_context
from app.services.classifier import LocalEmotionPrediction

logger = logging.getLogger(__name__)


class MessageAnalyzer:
    """Use the local classifier first and Foundry only for uncertain results."""

    def __init__(
        self,
        *,
        local_classifier: Any,
        fallback_classifier: Any | None,
        fallback_enabled: bool = True,
    ) -> None:
        self.local_classifier = local_classifier
        self.fallback_classifier = fallback_classifier
        self.fallback_enabled = fallback_enabled

    async def analyze(self, text: str) -> AnalysisResult:
        extracted = extract_context(text)
        try:
            local = self.local_classifier.classify(text)
        except Exception:
            # Missing/broken local model (e.g. ML deps not installed) must not
            # take down the whole chat turn — treat it the same as a
            # low-confidence local result so Foundry picks up the slack.
            logger.exception(
                "Local emotion classifier failed; falling back to Foundry classification"
            )
            local = LocalEmotionPrediction(
                emotion=None,
                confidence=0,
                emotion_scores={},
                requires_fallback=True,
            )

        if (
            local.requires_fallback
            and self.fallback_enabled
            and self.fallback_classifier is not None
        ):
            try:
                return await self.fallback_classifier.classify(text, extracted)
            except Exception:
                logger.exception(
                    "Foundry fallback failed; continuing with the local prediction"
                )

        if local.emotion is None:
            return AnalysisResult(
                emotion=Emotion.NEUTRAL,
                domains=extracted.domains,
                sleep_substances=extracted.sleep_substances,
                sleep_hours=extracted.sleep_hours,
                wake_time=extracted.wake_time,
                confidence=0,
                source=AnalysisSource.RULES,
                risk_level=RiskLevel.NONE,
                emotion_scores={},
                model_id=None,
                model_revision=None,
            )

        return AnalysisResult(
            emotion=local.emotion,
            domains=extracted.domains,
            sleep_substances=extracted.sleep_substances,
            sleep_hours=extracted.sleep_hours,
            wake_time=extracted.wake_time,
            confidence=local.confidence,
            source=AnalysisSource.LOCAL,
            risk_level=RiskLevel.NONE,
            emotion_scores=local.emotion_scores,
            model_id=self.local_classifier.model_id,
            model_revision=self.local_classifier.revision,
        )

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..schemas.analysis import Emotion
from .analysis_normalizer import normalize_emotion_label

PipelineFactory = Callable[..., Any]


@dataclass(frozen=True)
class LocalEmotionPrediction:
    emotion: Emotion | None
    confidence: float
    emotion_scores: dict[str, float]
    requires_fallback: bool


class LocalEmotionClassifier:
    def __init__(
        self,
        *,
        model_id: str,
        revision: str,
        confidence_threshold: float,
        device: str = "cpu",
        hf_token: str | None = None,
        pipeline_factory: PipelineFactory | None = None,
    ) -> None:
        if confidence_threshold < 0 or confidence_threshold > 1:
            raise ValueError("confidence_threshold must be between 0 and 1")
        self.model_id = model_id
        self.revision = revision
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.hf_token = hf_token
        self._pipeline_factory = pipeline_factory or _default_pipeline_factory
        self._pipeline: Any | None = None

    def classify(self, text: str) -> LocalEmotionPrediction:
        raw_output = self._get_pipeline()(
            text,
            top_k=None,
            truncation=True,
            max_length=512,
        )
        scores = _canonical_scores(raw_output)
        if not scores:
            return LocalEmotionPrediction(
                emotion=None,
                confidence=0,
                emotion_scores={},
                requires_fallback=True,
            )

        emotion_value, confidence = max(scores.items(), key=lambda item: item[1])
        emotion = Emotion(emotion_value)
        return LocalEmotionPrediction(
            emotion=emotion,
            confidence=confidence,
            emotion_scores=scores,
            requires_fallback=confidence < self.confidence_threshold,
        )

    def _get_pipeline(self) -> Any:
        if self._pipeline is None:
            kwargs: dict[str, Any] = {
                "model_id": self.model_id,
                "revision": self.revision,
                "device": self.device,
            }
            if self.hf_token:
                kwargs["hf_token"] = self.hf_token
            self._pipeline = self._pipeline_factory(**kwargs)
        return self._pipeline


def _default_pipeline_factory(
    *,
    model_id: str,
    revision: str,
    device: str,
    hf_token: str | None = None,
) -> Any:
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError(
            "Local emotion classification requires the ML dependencies. "
            "Install backend/requirements-ml.txt."
        ) from exc

    pipeline_device: int | str = -1 if device.casefold() == "cpu" else device
    kwargs: dict[str, Any] = {
        "task": "text-classification",
        "model": model_id,
        "revision": revision,
        "device": pipeline_device,
    }
    if hf_token:
        kwargs["token"] = hf_token
    return pipeline(**kwargs)


def _canonical_scores(raw_output: Any) -> dict[str, float]:
    rows = raw_output
    if isinstance(rows, dict):
        rows = [rows]
    if isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], list):
        rows = rows[0]
    if not isinstance(rows, list):
        return {}

    scores: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        emotion = normalize_emotion_label(str(row.get("label", "")))
        if emotion is None:
            continue
        try:
            score = float(row.get("score", 0))
        except (TypeError, ValueError):
            continue
        if score < 0 or score > 1:
            continue
        scores[emotion.value] = scores.get(emotion.value, 0) + score
    return scores

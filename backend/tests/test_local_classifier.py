import importlib
from typing import Any

import pytest


def _classifier_module():
    try:
        return importlib.import_module("app.services.classifier")
    except ModuleNotFoundError:
        pytest.fail("app.services.classifier is not implemented")


class FakePipeline:
    def __init__(self, output: list[dict[str, Any]]) -> None:
        self.output = output
        self.calls: list[str] = []

    def __call__(self, text: str, **_kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append(text)
        return self.output


def test_classifier_loads_the_model_lazily_and_reuses_it() -> None:
    classifier_module = _classifier_module()
    pipeline = FakePipeline(
        [
            {"label": "Senang", "score": 0.9},
            {"label": "Normal", "score": 0.1},
        ]
    )
    factory_calls: list[dict[str, Any]] = []

    def factory(**kwargs: Any) -> FakePipeline:
        factory_calls.append(kwargs)
        return pipeline

    classifier = classifier_module.LocalEmotionClassifier(
        model_id="model/name",
        revision="commit",
        confidence_threshold=0.65,
        pipeline_factory=factory,
    )
    assert factory_calls == []

    first = classifier.classify("Aku senang")
    second = classifier.classify("I am happy")

    assert len(factory_calls) == 1
    assert first.emotion.value == "joy"
    assert second.requires_fallback is False
    assert pipeline.calls == ["Aku senang", "I am happy"]


def test_classifier_aggregates_aliases_into_canonical_scores() -> None:
    classifier_module = _classifier_module()
    pipeline = FakePipeline(
        [
            {"label": "Marah", "score": 0.4},
            {"label": "Jengkel", "score": 0.35},
            {"label": "Normal", "score": 0.25},
        ]
    )
    classifier = classifier_module.LocalEmotionClassifier(
        model_id="model/name",
        revision="commit",
        confidence_threshold=0.65,
        pipeline_factory=lambda **_kwargs: pipeline,
    )

    result = classifier.classify("Kesal banget")

    assert result.emotion.value == "anger"
    assert result.confidence == pytest.approx(0.75)
    assert result.emotion_scores == {"anger": 0.75, "neutral": 0.25}
    assert result.requires_fallback is False


def test_low_confidence_prediction_requests_foundry_fallback() -> None:
    classifier_module = _classifier_module()
    pipeline = FakePipeline(
        [
            {"label": "Sedih", "score": 0.55},
            {"label": "Normal", "score": 0.45},
        ]
    )
    classifier = classifier_module.LocalEmotionClassifier(
        model_id="model/name",
        revision="commit",
        confidence_threshold=0.65,
        pipeline_factory=lambda **_kwargs: pipeline,
    )

    result = classifier.classify("Entahlah")

    assert result.emotion.value == "sadness"
    assert result.requires_fallback is True


def test_unmapped_prediction_requests_foundry_fallback() -> None:
    classifier_module = _classifier_module()
    pipeline = FakePipeline([{"label": "LABEL_404", "score": 0.99}])
    classifier = classifier_module.LocalEmotionClassifier(
        model_id="model/name",
        revision="commit",
        confidence_threshold=0.65,
        pipeline_factory=lambda **_kwargs: pipeline,
    )

    result = classifier.classify("Ambiguous")

    assert result.emotion is None
    assert result.confidence == 0
    assert result.requires_fallback is True

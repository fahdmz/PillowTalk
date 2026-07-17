import asyncio

from app.schemas.analysis import AnalysisResult, AnalysisSource, Domain, Emotion, RiskLevel
from app.services.analysis_service import MessageAnalyzer
from app.services.classifier import LocalEmotionPrediction, MissingMLDependenciesError


class FakeLocalClassifier:
    model_id = "local/model"
    revision = "abc123"

    def __init__(self, prediction: LocalEmotionPrediction) -> None:
        self.prediction = prediction
        self.calls: list[str] = []

    def classify(self, text: str) -> LocalEmotionPrediction:
        self.calls.append(text)
        return self.prediction


class FailingLocalClassifier:
    model_id = "local/model"
    revision = "abc123"

    def __init__(self, error: Exception) -> None:
        self.error = error

    def classify(self, text: str) -> LocalEmotionPrediction:
        raise self.error


class FakeFallbackClassifier:
    def __init__(self, result: AnalysisResult | None = None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls = []

    async def classify(self, text, extracted):
        self.calls.append((text, extracted))
        if self.error:
            raise self.error
        return self.result


def local_prediction(*, emotion=Emotion.JOY, confidence=0.91, fallback=False):
    return LocalEmotionPrediction(
        emotion=emotion,
        confidence=confidence,
        emotion_scores={} if emotion is None else {emotion.value: confidence},
        requires_fallback=fallback,
    )


def foundry_result() -> AnalysisResult:
    return AnalysisResult(
        emotion=Emotion.SADNESS,
        domains=[Domain.WORK],
        sleep_substances=[],
        sleep_hours=None,
        wake_time=None,
        confidence=0.88,
        source=AnalysisSource.FOUNDRY_FALLBACK,
        risk_level=RiskLevel.NONE,
        emotion_scores={"sadness": 0.88},
        model_id="gpt-fallback",
        model_revision=None,
    )


def test_high_confidence_local_prediction_skips_foundry_and_keeps_extraction():
    local = FakeLocalClassifier(local_prediction())
    fallback = FakeFallbackClassifier(foundry_result())
    analyzer = MessageAnalyzer(local_classifier=local, fallback_classifier=fallback)

    result = asyncio.run(analyzer.analyze("Aku minum kopi dan tidur 6 jam"))

    assert result.emotion is Emotion.JOY
    assert result.source is AnalysisSource.LOCAL
    assert result.sleep_hours == 6
    assert Domain.SLEEP in result.domains
    assert fallback.calls == []


def test_uncertain_local_prediction_uses_foundry_fallback():
    local = FakeLocalClassifier(local_prediction(confidence=0.42, fallback=True))
    fallback = FakeFallbackClassifier(foundry_result())
    analyzer = MessageAnalyzer(local_classifier=local, fallback_classifier=fallback)

    result = asyncio.run(analyzer.analyze("Pekerjaan hari ini rasanya campur aduk"))

    assert result.emotion is Emotion.SADNESS
    assert result.source is AnalysisSource.FOUNDRY_FALLBACK
    assert len(fallback.calls) == 1


def test_missing_ml_dependencies_use_foundry_fallback_without_crashing():
    local = FailingLocalClassifier(
        MissingMLDependenciesError("Install backend/requirements-ml.txt.")
    )
    fallback = FakeFallbackClassifier(foundry_result())
    analyzer = MessageAnalyzer(local_classifier=local, fallback_classifier=fallback)

    result = asyncio.run(analyzer.analyze("Aku capek karena kerja"))

    assert result.emotion is Emotion.SADNESS
    assert result.source is AnalysisSource.FOUNDRY_FALLBACK
    assert len(fallback.calls) == 1


def test_foundry_failure_degrades_to_mapped_local_prediction():
    local = FakeLocalClassifier(local_prediction(confidence=0.4, fallback=True))
    fallback = FakeFallbackClassifier(error=TimeoutError("Foundry timed out"))
    analyzer = MessageAnalyzer(local_classifier=local, fallback_classifier=fallback)

    result = asyncio.run(analyzer.analyze("Aku senang, tapi juga bingung"))

    assert result.emotion is Emotion.JOY
    assert result.source is AnalysisSource.LOCAL
    assert result.confidence == 0.4


def test_unmapped_local_prediction_without_fallback_returns_neutral_rules_result():
    local = FakeLocalClassifier(local_prediction(emotion=None, confidence=0, fallback=True))
    analyzer = MessageAnalyzer(
        local_classifier=local,
        fallback_classifier=None,
        fallback_enabled=False,
    )

    result = asyncio.run(analyzer.analyze("Sesuatu terjadi"))

    assert result.emotion is Emotion.NEUTRAL
    assert result.source is AnalysisSource.RULES
    assert result.model_id is None

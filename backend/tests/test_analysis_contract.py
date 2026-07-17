import importlib

import pytest
from pydantic import ValidationError


def _analysis_module():
    try:
        return importlib.import_module("app.schemas.analysis")
    except ModuleNotFoundError:
        pytest.fail("app.schemas.analysis is not implemented")


def test_analysis_result_accepts_the_canonical_contract() -> None:
    analysis = _analysis_module()

    result = analysis.AnalysisResult(
        emotion="joy",
        domains=["sleep", "sleep_substances"],
        sleep_substances=["caffeine"],
        sleep_hours=6.5,
        wake_time="06:30",
        confidence=0.91,
        source="local",
        risk_level="none",
        emotion_scores={"joy": 0.91, "neutral": 0.09},
        model_id="model/name",
        model_revision="commit",
    )

    assert result.emotion.value == "joy"
    assert result.wake_time == "06:30"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("emotion", "disgust"),
        ("domains", ["finance"]),
        ("sleep_substances", ["sugar"]),
        ("confidence", 1.1),
        ("sleep_hours", 25),
        ("wake_time", "6:30 AM"),
    ],
)
def test_analysis_result_rejects_values_outside_the_contract(
    field: str,
    value: object,
) -> None:
    analysis = _analysis_module()
    payload = {
        "emotion": "neutral",
        "domains": [],
        "sleep_substances": [],
        "sleep_hours": None,
        "wake_time": None,
        "confidence": 0.5,
        "source": "rules",
        "risk_level": "none",
        "emotion_scores": {},
        "model_id": None,
        "model_revision": None,
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        analysis.AnalysisResult(**payload)

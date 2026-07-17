import importlib

import pytest


def _normalizer_module():
    try:
        return importlib.import_module("app.services.analysis_normalizer")
    except ModuleNotFoundError:
        pytest.fail("app.services.analysis_normalizer is not implemented")


@pytest.mark.parametrize(
    ("raw_label", "expected"),
    [
        ("Senang", "joy"),
        ("Happy", "joy"),
        ("Sedih", "sadness"),
        ("Marah", "anger"),
        ("Takut", "fear"),
        ("Terkejut", "surprise"),
        ("Cinta", "love"),
        ("Normal", "neutral"),
        ("LABEL_404", None),
    ],
)
def test_normalizes_indonesian_and_english_model_labels(
    raw_label: str,
    expected: str | None,
) -> None:
    normalizer = _normalizer_module()

    result = normalizer.normalize_emotion_label(raw_label)

    assert (result.value if result else None) == expected


def test_extracts_mixed_indonesian_sleep_context() -> None:
    normalizer = _normalizer_module()

    result = normalizer.extract_context(
        "Semalam aku minum kopi karena deadline kerja, tidur 5,5 jam dan bangun jam 06.15."
    )

    assert result.sleep_hours == 5.5
    assert result.wake_time == "06:15"
    assert result.domains == ["sleep", "work", "sleep_substances"]
    assert result.sleep_substances == ["caffeine"]


def test_extracts_english_sleep_medication_context() -> None:
    normalizer = _normalizer_module()

    result = normalizer.extract_context(
        "I took a sleeping pill, slept 7 hours, and woke up at 7:20."
    )

    assert result.sleep_hours == 7.0
    assert result.wake_time == "07:20"
    assert result.domains == ["sleep", "health", "sleep_substances"]
    assert result.sleep_substances == ["sleep_medication"]


def test_does_not_record_a_negated_substance() -> None:
    normalizer = _normalizer_module()

    result = normalizer.extract_context("Aku tidak minum kopi malam ini.")

    assert result.sleep_substances == []
    assert "sleep_substances" not in result.domains

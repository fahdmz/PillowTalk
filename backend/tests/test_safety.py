import pytest

from app.schemas.analysis import RiskLevel
from app.services.safety import SafetyScreen, build_safety_message


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Aku sedih dan capek sekali hari ini", RiskLevel.NONE),
        ("Deadline ini membunuhku wkwk", RiskLevel.NONE),
        ("Aku tidak ingin bunuh diri", RiskLevel.NONE),
        ("Dulu aku pernah ingin mati, tapi sekarang aku aman", RiskLevel.LOW),
        ('Temanku berkata "aku ingin mati" dan aku bingung membantunya', RiskLevel.LOW),
        ("Aku mau bunuh diri malam ini", RiskLevel.CRITICAL),
        ("Aku punya pisau dan akan menyakiti diriku sekarang", RiskLevel.CRITICAL),
        ("Aku akan membunuh dia malam ini", RiskLevel.CRITICAL),
    ],
)
def test_bilingual_rule_screen_distinguishes_current_intent_from_context(text, expected):
    result = SafetyScreen().screen(text)

    assert result.risk_level is expected
    assert result.should_interrupt is (expected in {RiskLevel.HIGH, RiskLevel.CRITICAL})


def test_safety_result_exposes_auditable_signal_codes_without_message_copy():
    result = SafetyScreen().screen("Aku ingin mati sekarang")

    assert result.risk_level is RiskLevel.CRITICAL
    assert "self_harm_intent" in result.signal_codes
    assert "immediacy" in result.signal_codes
    assert not hasattr(result, "text")


def test_indonesian_safety_message_is_direct_and_uses_configured_resources():
    message = build_safety_message(
        language="id",
        resource_name="Healing119",
        resource_phone="119 ext. 8",
        resource_url="https://www.healing119.id",
    )

    assert message.is_crisis is True
    assert "119 ext. 8" in message.text
    assert "https://www.healing119.id" in message.text
    assert "orang yang kamu percaya" in message.text
    assert "darurat" in message.text.casefold()
    assert "24 jam" not in message.text.casefold()

import pytest

from app.schemas.analysis import RiskLevel
from app.services.safety import SafetyScreen


@pytest.mark.parametrize(
    "text",
    [
        "Dulu aku pernah ingin mati, tapi sekarang aku mau bunuh diri malam ini",
        "My friend said he wanted to die, but I want to kill myself tonight",
    ],
)
def test_current_intent_overrides_historical_or_third_person_context(text):
    result = SafetyScreen().screen(text)

    assert result.risk_level is RiskLevel.CRITICAL
    assert result.should_interrupt is True

"""Deterministic bilingual safety screening before any model call.

This is a conservative routing aid, not a clinical assessment. Only current,
first-person self-harm intent or an imminent threat interrupts normal chat.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from app.schemas.analysis import RiskLevel

Language = Literal["en", "id"]

_SELF_HARM_PATTERNS = (
    r"\bbunuh diri\b",
    r"\b(?:aku|saya|gue|gw) (?:pernah )?(?:ingin|mau|pengen|akan) mati\b",
    r"\b(?:aku|saya|gue|gw) (?:akan |mau |ingin )?(?:menyakiti|melukai) diri\b",
    r"\bkill myself\b",
    r"\b(?:i )?(?:want|wanna|plan|going) to die\b",
    r"\bend my life\b",
    r"\bhurt myself\b",
    r"\bself[- ]harm\b",
    r"\b(?:menyakiti|melukai) diri(?:ku)?\b",
)
_VIOLENCE_PATTERNS = (
    r"\b(?:aku|saya|gue|gw) akan membunuh (?:dia|mereka|kamu)\b",
    r"\bi (?:will|am going to) kill (?:him|her|them|you)\b",
)
_IMMEDIACY_PATTERN = re.compile(
    r"\b(?:sekarang|malam ini|hari ini|sebentar lagi|now|tonight|today|soon)\b"
)
_MEANS_PATTERN = re.compile(
    r"\b(?:pisau|pistol|senjata|tali|racun|knife|gun|weapon|rope|poison)\b"
)
_CLAUSE_BREAK_PATTERN = re.compile(
    r"\b(?:tapi|tetapi|namun|but|however)\b|[.!?]+|,(?=\s*(?:sekarang|now)\b)"
)
_NEGATIONS = frozenset(
    {"tidak", "nggak", "enggak", "gak", "ga", "bukan", "tak", "no", "not", "never"}
)
_HISTORICAL_MARKERS = (
    "dulu",
    "pernah",
    "waktu itu",
    "in the past",
    "used to",
    "previously",
)
_CURRENT_SAFE_MARKERS = (
    "sekarang aku aman",
    "sekarang saya aman",
    "aku sudah aman",
    "i am safe now",
    "i'm safe now",
)
_THIRD_PERSON_MARKERS = (
    "temanku berkata",
    "teman saya berkata",
    "dia berkata",
    "my friend said",
    "they said",
    "he said",
    "she said",
)
_RISK_RANK = {
    RiskLevel.NONE: 0,
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}


@dataclass(frozen=True)
class SafetyResult:
    risk_level: RiskLevel
    signal_codes: tuple[str, ...]

    @property
    def should_interrupt(self) -> bool:
        return self.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}


@dataclass(frozen=True)
class SafetyMessage:
    text: str
    is_crisis: bool = True


class SafetyScreen:
    def screen(self, text: str) -> SafetyResult:
        normalized = unicodedata.normalize("NFKC", text).casefold()
        clauses = [
            clause.strip(" ,;:\t\n\r\"'")
            for clause in _CLAUSE_BREAK_PATTERN.split(normalized)
            if clause.strip(" ,;:\t\n\r\"'")
        ]
        results = [_screen_clause(clause) for clause in clauses or [normalized]]
        return max(results, key=lambda result: _RISK_RANK[result.risk_level])


def _screen_clause(text: str) -> SafetyResult:
    self_harm = _contains_unnegated(text, _SELF_HARM_PATTERNS)
    violence = _contains_unnegated(text, _VIOLENCE_PATTERNS)
    if not self_harm and not violence:
        return SafetyResult(RiskLevel.NONE, ())

    signals: list[str] = []
    if self_harm:
        signals.append("self_harm_intent")
    if violence:
        signals.append("violence_intent")

    contextual = any(marker in text for marker in _HISTORICAL_MARKERS)
    contextual = contextual or any(marker in text for marker in _THIRD_PERSON_MARKERS)
    safe_now = any(marker in text for marker in _CURRENT_SAFE_MARKERS)
    if contextual or safe_now:
        signals.append("contextual_or_historical")
        return SafetyResult(RiskLevel.LOW, tuple(signals))

    if _IMMEDIACY_PATTERN.search(text):
        signals.append("immediacy")
    if _MEANS_PATTERN.search(text):
        signals.append("means_access")

    risk = (
        RiskLevel.CRITICAL
        if "immediacy" in signals or "means_access" in signals
        else RiskLevel.HIGH
    )
    return SafetyResult(risk, tuple(signals))


def build_safety_message(
    *,
    language: Language,
    resource_name: str,
    resource_phone: str,
    resource_url: str,
) -> SafetyMessage:
    if language == "id":
        text = (
            "Terima kasih sudah memberitahuku. Aku khawatir kamu mungkin berada "
            "dalam bahaya sekarang. Tolong jauhkan benda atau obat yang bisa "
            "melukaimu, hubungi orang yang kamu percaya agar menemanimu, dan "
            "hubungi layanan darurat 119 bila bahayanya segera. Kamu juga dapat "
            f"menghubungi {resource_name} di {resource_phone} atau {resource_url}."
        )
    else:
        text = (
            "Thank you for telling me. I'm concerned you may be in immediate "
            "danger. Move away from anything you could use to hurt yourself, ask "
            "someone you trust to stay with you, and call emergency service 119 "
            f"if the danger is immediate. You can also contact {resource_name} at "
            f"{resource_phone} or {resource_url}."
        )
    return SafetyMessage(text=text)


def _contains_unnegated(text: str, patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            preceding_tokens = re.findall(r"\b\w+\b", text[: match.start()])[-4:]
            matched_tokens = re.findall(r"\b\w+\b", match.group(0))
            if not any(token in _NEGATIONS for token in preceding_tokens + matched_tokens):
                return True
    return False

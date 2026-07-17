"""Rule-based crisis detection.

Deliberately NOT LLM-based: per product scope, crisis routing must be
deterministic and auditable. This is a keyword screen, not a clinical
assessment — it is tuned to be sensitive (over-trigger) rather than
specific, since the cost of a false positive (one extra check-in message) is
far lower than missing a real crisis message.
"""

from typing import Literal

Language = Literal["en", "id"]

_CRISIS_KEYWORDS = [
    # English
    "kill myself", "suicide", "end my life", "want to die", "wanna die",
    "hurt myself", "self harm", "self-harm", "not want to live",
    "no reason to live", "better off dead",
    # Indonesian
    "bunuh diri", "mengakhiri hidup", "ingin mati", "mau mati",
    "menyakiti diri", "melukai diri", "tidak ingin hidup",
    "tidak ada alasan untuk hidup", "lebih baik mati",
]

# SEJIWA — Indonesia's free 24-hour mental health crisis line.
_CRISIS_PHONE = "119 ext. 8"

_CRISIS_PREFIX: dict[Language, str] = {
    "en": (
        "I'm really glad you told me, and I'm concerned about you. "
        "You don't have to go through this alone. You can call or WhatsApp "
    ),
    "id": (
        "Aku senang kamu memberitahuku, dan aku khawatir tentangmu. "
        "Kamu tidak harus melewati ini sendirian. Kamu bisa menelepon atau WhatsApp "
    ),
}

_CRISIS_SUFFIX: dict[Language, str] = {
    "en": (
        " (SEJIWA, Indonesia's free 24-hour mental health crisis line) to talk with someone "
        "who can help. Would you like to talk about what's been going on?"
    ),
    "id": (
        " (SEJIWA, layanan krisis kesehatan mental gratis 24 jam di Indonesia) untuk berbicara "
        "dengan seseorang yang bisa membantu. Apakah kamu ingin bercerita lebih lanjut tentang "
        "apa yang terjadi?"
    ),
}


def detect_crisis(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in _CRISIS_KEYWORDS)


def crisis_message_fields(language: Language) -> dict:
    """Fields to insert into chat_messages for the hard-stop crisis reply."""
    lang: Language = language if language in ("en", "id") else "en"
    return {
        "text": None,
        "is_crisis": True,
        "crisis_prefix": _CRISIS_PREFIX[lang],
        "crisis_phone": _CRISIS_PHONE,
        "crisis_suffix": _CRISIS_SUFFIX[lang],
    }

import re
import unicodedata

from ..schemas.analysis import Domain, Emotion, ExtractedContext, SleepSubstance

_LABEL_MAP: dict[str, Emotion] = {
    "joy": Emotion.JOY,
    "happy": Emotion.JOY,
    "happiness": Emotion.JOY,
    "senang": Emotion.JOY,
    "sad": Emotion.SADNESS,
    "sadness": Emotion.SADNESS,
    "sedih": Emotion.SADNESS,
    "lelah": Emotion.SADNESS,
    "anger": Emotion.ANGER,
    "angry": Emotion.ANGER,
    "marah": Emotion.ANGER,
    "jengkel": Emotion.ANGER,
    "frustrasi": Emotion.ANGER,
    "fear": Emotion.FEAR,
    "afraid": Emotion.FEAR,
    "takut": Emotion.FEAR,
    "surprise": Emotion.SURPRISE,
    "surprised": Emotion.SURPRISE,
    "terkejut": Emotion.SURPRISE,
    "kaget": Emotion.SURPRISE,
    "love": Emotion.LOVE,
    "cinta": Emotion.LOVE,
    "neutral": Emotion.NEUTRAL,
    "netral": Emotion.NEUTRAL,
    "normal": Emotion.NEUTRAL,
    "sabar": Emotion.NEUTRAL,
}

_DOMAIN_KEYWORDS: dict[Domain, tuple[str, ...]] = {
    Domain.RELATIONSHIP: (
        "pacar",
        "pasangan",
        "suami",
        "istri",
        "relationship",
        "boyfriend",
        "girlfriend",
        "partner",
    ),
    Domain.SLEEP: (
        "tidur",
        "bangun",
        "insomnia",
        "sleep",
        "slept",
        "woke",
        "awake",
    ),
    Domain.WORK: (
        "kerja",
        "kantor",
        "deadline",
        "rapat",
        "meeting",
        "work",
        "office",
    ),
    Domain.HEALTH: (
        "sakit",
        "kesehatan",
        "nyeri",
        "dokter",
        "obat",
        "health",
        "sick",
        "pain",
        "pill",
        "medication",
    ),
}

_SUBSTANCE_KEYWORDS: dict[SleepSubstance, tuple[str, ...]] = {
    SleepSubstance.CAFFEINE: (
        "energy drink",
        "minuman energi",
        "kafein",
        "caffeine",
        "coffee",
        "kopi",
    ),
    SleepSubstance.ALCOHOL: ("alkohol", "alcohol", "beer", "bir", "wine"),
    SleepSubstance.NICOTINE: (
        "nikotin",
        "nicotine",
        "rokok",
        "merokok",
        "vape",
        "cigarette",
    ),
    SleepSubstance.SLEEP_MEDICATION: (
        "sleeping pill",
        "obat tidur",
        "melatonin",
        "zolpidem",
    ),
    SleepSubstance.OTHER_STIMULANT: (
        "stimulan",
        "stimulant",
        "amfetamin",
        "amphetamine",
    ),
    SleepSubstance.OTHER_SEDATIVE: (
        "obat penenang",
        "penenang",
        "sedatif",
        "sedative",
        "benzodiazepine",
    ),
}

_NEGATIONS = frozenset(
    {"tidak", "nggak", "enggak", "gak", "ga", "belum", "tanpa", "no", "not", "didnt"}
)
_DOMAIN_ORDER = tuple(Domain)
_SUBSTANCE_ORDER = tuple(SleepSubstance)
_SLEEP_HOURS_PATTERN = re.compile(
    r"\b(?:tidur|slept|sleep(?:ing)?)\s+(?:selama\s+|for\s+)?"
    r"(?P<hours>\d{1,2}(?:[.,]\d+)?)\s*(?:jam|hours?|hrs?)\b",
    re.IGNORECASE,
)
_WAKE_TIME_PATTERN = re.compile(
    r"\b(?:bangun(?:\s+tidur)?|woke\s+up|wake\s+up)\s*"
    r"(?:jam|pukul|at)?\s*(?P<hour>\d{1,2})(?:[.:](?P<minute>\d{2}))?\b",
    re.IGNORECASE,
)


def normalize_emotion_label(raw_label: str) -> Emotion | None:
    normalized = unicodedata.normalize("NFKC", raw_label).strip().casefold()
    normalized = re.sub(r"[\s_-]+", " ", normalized)
    return _LABEL_MAP.get(normalized)


def extract_context(text: str) -> ExtractedContext:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    substances = [
        substance
        for substance in _SUBSTANCE_ORDER
        if _contains_non_negated_keyword(normalized, _SUBSTANCE_KEYWORDS[substance])
    ]

    detected_domains = {
        domain
        for domain, keywords in _DOMAIN_KEYWORDS.items()
        if any(_contains_keyword(normalized, keyword) for keyword in keywords)
    }
    if substances:
        detected_domains.add(Domain.SLEEP_SUBSTANCES)

    return ExtractedContext(
        domains=[domain for domain in _DOMAIN_ORDER if domain in detected_domains],
        sleep_substances=[
            substance for substance in _SUBSTANCE_ORDER if substance in substances
        ],
        sleep_hours=_extract_sleep_hours(normalized),
        wake_time=_extract_wake_time(normalized),
    )


def _contains_keyword(text: str, keyword: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text) is not None


def _contains_non_negated_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    for keyword in keywords:
        for match in re.finditer(rf"(?<!\w){re.escape(keyword)}(?!\w)", text):
            preceding_tokens = re.findall(r"\b\w+\b", text[: match.start()])[-4:]
            if not any(token in _NEGATIONS for token in preceding_tokens):
                return True
    return False


def _extract_sleep_hours(text: str) -> float | None:
    match = _SLEEP_HOURS_PATTERN.search(text)
    if match is None:
        return None
    return float(match.group("hours").replace(",", "."))


def _extract_wake_time(text: str) -> str | None:
    match = _WAKE_TIME_PATTERN.search(text)
    if match is None:
        return None
    hour = int(match.group("hour"))
    minute = int(match.group("minute") or "0")
    if hour > 23 or minute > 59:
        return None
    return f"{hour:02d}:{minute:02d}"

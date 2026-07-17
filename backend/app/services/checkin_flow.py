"""Fixed-step check-in state machines.

Per product scope: check-ins are NOT open-ended LLM conversation. Question
order and count are deterministic per check-in type, so crisis routing,
consent, and the flow's length stay predictable and reviewable. If an LLM is
ever introduced (e.g. to vary phrasing), it must not be able to change the
step order, skip steps, or suppress the crisis check in chat.py.
"""

from typing import Literal

CheckinMode = Literal["night", "morning"]
Language = Literal["en", "id"]

GREETINGS: dict[CheckinMode, dict[Language, str]] = {
    "night": {
        "en": "Hi, I'm here. What's on your mind tonight?",
        "id": "Hai, aku di sini. Apa yang sedang kamu pikirkan malam ini?",
    },
    "morning": {
        "en": "Good morning. How did you sleep?",
        "id": "Selamat pagi. Bagaimana tidurmu semalam?",
    },
}

# Each string is the AI's reply after the user's message at that step index.
# The nightly flow is capped at 3 exchanges and always ends in a wind-down
# closer. The morning flow walks a Consensus-Sleep-Diary-lite set of
# questions (bedtime/latency, wake-ups, wake time + quality).
_NIGHT_STEPS: dict[Language, list[str]] = {
    "en": [
        "That sounds like it's been weighing on you. Want to tell me more?",
        "I hear you. Sometimes naming it helps it feel lighter. Anything else on your mind?",
        "Thank you for sharing that. Let's set it down for tonight — it'll be there tomorrow. "
        "Take a slow breath with me before you sleep.",
    ],
    "id": [
        "Sepertinya itu cukup membebani pikiranmu. Mau cerita lebih lanjut?",
        "Aku mendengarmu. Kadang menyebutkannya membuatnya terasa lebih ringan. "
        "Ada hal lain yang mengganggu pikiranmu?",
        "Terima kasih sudah berbagi. Mari kita simpan dulu untuk malam ini — itu akan tetap ada besok. "
        "Ambil napas perlahan bersamaku sebelum tidur.",
    ],
}

_MORNING_STEPS: dict[Language, list[str]] = {
    "en": [
        "Thanks for sharing. What time did you get into bed, and about how long did it take to fall asleep?",
        "Got it. Did you wake up during the night? If so, about how many times, and for how long in total?",
        "Thanks. What time did you finally wake up, and how would you rate your sleep quality "
        "from 1 (poor) to 5 (great)?",
        "That's really useful, thank you. Have a gentle day.",
    ],
    "id": [
        "Terima kasih sudah berbagi. Jam berapa kamu masuk ke tempat tidur, dan kira-kira berapa lama untuk tertidur?",
        "Baik. Apakah kamu terbangun di malam hari? Jika ya, berapa kali dan berapa lama total?",
        "Terima kasih. Jam berapa kamu akhirnya bangun, dan bagaimana kamu menilai kualitas tidurmu "
        "dari 1 (buruk) hingga 5 (sangat baik)?",
        "Itu sangat berguna, terima kasih. Semoga harimu menyenangkan.",
    ],
}

_STEPS: dict[CheckinMode, dict[Language, list[str]]] = {
    "night": _NIGHT_STEPS,
    "morning": _MORNING_STEPS,
}


def greeting_for(mode: CheckinMode, language: Language) -> str:
    lang = language if language in ("en", "id") else "en"
    return GREETINGS[mode][lang]


def next_step_reply(mode: CheckinMode, step_index: int, language: Language) -> tuple[str, bool]:
    """Returns (reply_text, is_final_step). is_final_step tells the caller
    to mark the session completed after this reply is sent."""
    lang = language if language in ("en", "id") else "en"
    steps = _STEPS[mode][lang]
    index = min(step_index, len(steps) - 1)
    return steps[index], index == len(steps) - 1

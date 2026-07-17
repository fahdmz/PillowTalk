"""Generate one cautious, structured Indonesian recap for a completed session."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from app.schemas.analysis import Domain, Emotion

PROMPT_VERSION = "recap-id-v2"

_INSTRUCTIONS = """Buat satu rangkuman check-in PillowTalk dalam bahasa Indonesia alami.
Gunakan hanya transkrip dan hasil analisis yang diberikan. Jangan mendiagnosis, jangan
memberikan nasihat medis, dan jangan menyatakan hubungan sebab-akibat. Bedakan dengan
jelas antara hal yang dilaporkan pengguna dan pengamatan yang masih mungkin. Tulis dengan
hangat, ringkas, tidak menghakimi. Jangan menambahkan fakta, emosi, zat, jam tidur, atau
waktu bangun yang tidak ada dalam masukan.

Sudut pandang wajib: tulis SELALU dari sudut pandang pengguna, dengan "kamu" sebagai
subjek di hampir setiap kalimat. Rangkuman ini milik pengguna, bukan catatan asisten AI.
Jangan pernah menulis dari sudut pandang AI atau menyebut tindakan AI/asisten (seperti
"saya bertanya", "saya menanyakan", "asisten merespons", atau "aku menyarankan"). Jangan
gunakan kata "saya", "aku", atau "asisten" sama sekali.

Salah (sudut pandang AI, dilarang): "Saya tanya user tentang tidurnya, lalu saya
menyarankan teknik pernapasan."
Benar (sudut pandang pengguna, wajib): "Kamu bercerita tentang tidur yang terganggu
karena pikiran soal kerjaan, lalu mencoba teknik pernapasan singkat untuk lebih
tenang.\""""


class EmotionalTrend(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: Literal["membaik", "memburuk", "stabil", "campuran", "tidak_cukup_data"]
    observation: str


class RecapOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    summary: str
    conclusion: str
    dominant_emotion: Emotion | None
    domains: list[Domain]
    emotional_trend: EmotionalTrend
    sleep_observations: list[str]


class RecapGenerationError(RuntimeError):
    pass


class FoundryRecapGenerator:
    def __init__(
        self,
        *,
        client: Any,
        deployment: str,
        max_output_tokens: int = 500,
    ) -> None:
        self.client = client
        self.deployment = deployment
        self.max_output_tokens = max_output_tokens

    async def generate(
        self,
        *,
        checkin_mode: str,
        messages: list[dict[str, Any]],
        analyses: list[dict[str, Any]],
    ) -> RecapOutput:
        payload = {
            "checkin_mode": checkin_mode,
            "transcript": messages,
            "message_analyses": analyses,
        }
        response = await self.client.responses.create(
            model=self.deployment,
            instructions=_INSTRUCTIONS,
            input=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "pillowtalk_session_recap",
                    "description": "Rangkuman terstruktur untuk satu sesi PillowTalk.",
                    "schema": RecapOutput.model_json_schema(),
                    "strict": True,
                }
            },
            store=False,
            max_output_tokens=self.max_output_tokens,
            # Same fix as foundry_chatbot.py/fallback_classifier.py: structured
            # summarization against a fixed schema doesn't need deep
            # reasoning, and without capping effort, gpt-5's default can eat
            # the whole max_output_tokens budget before writing the JSON.
            reasoning={"effort": "low"},
        )
        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise RecapGenerationError("Azure AI Foundry returned an empty recap")
        try:
            return RecapOutput.model_validate_json(output_text)
        except ValidationError as exc:
            raise RecapGenerationError(
                "Azure AI Foundry returned an invalid recap"
            ) from exc

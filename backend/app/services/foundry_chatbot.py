"""Azure AI Foundry chatbot client with bounded application-owned context."""

from __future__ import annotations

import json
from typing import Any

from app.schemas.analysis import AnalysisResult

_INDONESIAN_INSTRUCTIONS = """Kamu adalah teman check-in tidur PillowTalk yang hangat,
ringkas, dan tidak menghakimi. Jawab dalam bahasa Indonesia alami, kecuali pengguna jelas
memilih bahasa Inggris. Gunakan konteks hanya untuk kesinambungan. Jangan mendiagnosis,
jangan memberikan nasihat medis, dan jangan menyatakan hubungan sebab-akibat dari pola
emosi, zat, atau tidur. Sebut pola sebagai pengamatan yang mungkin. Ajukan paling banyak
satu pertanyaan yang lembut. Jangan mengklaim mengingat hal di luar konteks yang diberikan."""

_ENGLISH_INSTRUCTIONS = """You are PillowTalk's warm, concise, non-judgmental sleep
check-in companion. Use the supplied context only for continuity. Do not diagnose, give
medical advice, or claim that an emotion, substance, or behavior caused a sleep outcome.
Describe patterns only as tentative observations. Ask at most one gentle question. Never
claim to remember anything outside the supplied context."""


class FoundryChatError(RuntimeError):
    pass


class FoundryChatbot:
    def __init__(
        self,
        *,
        client: Any,
        deployment: str,
        max_output_tokens: int = 800,
    ) -> None:
        self.client = client
        self.deployment = deployment
        self.max_output_tokens = max_output_tokens

    async def respond(
        self,
        *,
        language: str,
        checkin_mode: str,
        user_message: str,
        analysis: AnalysisResult,
        context: dict[str, Any],
    ) -> str:
        payload = {
            "checkin_mode": checkin_mode,
            "current_message": user_message,
            "current_analysis": analysis.model_dump(mode="json"),
            "bounded_context": context,
        }
        response = await self.client.responses.create(
            model=self.deployment,
            instructions=(
                _INDONESIAN_INSTRUCTIONS if language == "id" else _ENGLISH_INSTRUCTIONS
            ),
            input=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            store=False,
            max_output_tokens=self.max_output_tokens,
        )
        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise FoundryChatError("Azure AI Foundry returned an empty chat response")
        return output_text.strip()

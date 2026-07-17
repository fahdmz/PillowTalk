"""Azure AI Foundry chatbot client with bounded application-owned context."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from app.schemas.analysis import AnalysisResult

_INDONESIAN_INSTRUCTIONS = """Kamu adalah teman check-in tidur PillowTalk yang hangat,
ringkas, dan tidak menghakimi. Jawab dalam bahasa Indonesia alami, kecuali pengguna jelas
memilih bahasa Inggris. Gunakan konteks hanya untuk kesinambungan. Jangan mendiagnosis,
jangan memberikan nasihat medis, dan jangan menyatakan hubungan sebab-akibat dari pola
emosi, zat, atau tidur. Sebut pola sebagai pengamatan yang mungkin. Ajukan paling banyak
satu pertanyaan yang lembut. Jangan mengklaim mengingat hal di luar konteks yang diberikan.

Percakapan ini punya batas waktu, bukan obrolan terbuka tanpa akhir — check-in malam
maupun pagi harus terasa singkat dan tuntas, bukan berlarut-larut. Set should_close=true
pada balasanmu HANYA ketika percakapan terasa sudah mencapai penutupan alami: untuk
check-in malam, biasanya setelah kamu menawarkan satu teknik menenangkan (napas, brain
dump, dsb.) dan pengguna terdengar cukup atau siap tidur; untuk check-in pagi, biasanya
setelah pengguna menceritakan tidurnya dan kamu memberi satu refleksi singkat. Jangan
menutup di balasan pertamamu atau sebelum pengguna sempat bercerita sedikit — beri
percakapan setidaknya dua atau tiga pertukaran pesan dulu. Ketika should_close=true,
akhiri reply-mu dengan kalimat penutup yang hangat (bukan pertanyaan baru)."""

_ENGLISH_INSTRUCTIONS = """You are PillowTalk's warm, concise, non-judgmental sleep
check-in companion. Use the supplied context only for continuity. Do not diagnose, give
medical advice, or claim that an emotion, substance, or behavior caused a sleep outcome.
Describe patterns only as tentative observations. Ask at most one gentle question. Never
claim to remember anything outside the supplied context.

This conversation is bounded, not an open-ended chat — both night and morning check-ins
should feel short and complete, not endless. Set should_close=true on your reply ONLY
when the conversation feels like it has reached a natural close: for a night check-in,
usually after you've offered one calming technique (breathing, brain dump, etc.) and the
user sounds settled or ready for sleep; for a morning check-in, usually after the user
has shared how they slept and you've offered one brief reflection. Don't close on your
very first reply, and give the conversation at least two or three exchanges first. When
should_close=true, end your reply with a warm closing line rather than a new question."""


class ChatReplyOutput(BaseModel):
    """Strict output contract for one chat turn."""

    model_config = ConfigDict(extra="forbid")

    reply: str
    should_close: bool


@dataclass(frozen=True)
class ChatbotReply:
    text: str
    should_close: bool


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
    ) -> ChatbotReply:
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
            text={
                "format": {
                    "type": "json_schema",
                    "name": "pillowtalk_chat_reply",
                    "strict": True,
                    "schema": ChatReplyOutput.model_json_schema(),
                }
            },
            store=False,
            max_output_tokens=self.max_output_tokens,
            # A warm chat reply doesn't need deep multi-step reasoning, and
            # gpt-5's default reasoning effort can burn the entire
            # max_output_tokens budget on internal reasoning tokens before
            # any visible text is written, leaving output_text empty.
            reasoning={"effort": "low"},
        )
        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise FoundryChatError("Azure AI Foundry returned an empty chat response")
        try:
            parsed = ChatReplyOutput.model_validate_json(output_text)
        except ValidationError as exc:
            raise FoundryChatError("Azure AI Foundry returned an invalid chat reply") from exc
        if not parsed.reply.strip():
            raise FoundryChatError("Azure AI Foundry returned an empty chat response")
        return ChatbotReply(text=parsed.reply.strip(), should_close=parsed.should_close)

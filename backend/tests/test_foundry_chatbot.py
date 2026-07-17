import asyncio
from types import SimpleNamespace

import pytest

from app.schemas.analysis import AnalysisResult, AnalysisSource, Emotion, RiskLevel
from app.services.foundry_chatbot import FoundryChatbot, FoundryChatError


class FakeResponses:
    def __init__(self, output_text):
        self.output_text = output_text
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=self.output_text)


def analysis():
    return AnalysisResult(
        emotion=Emotion.SADNESS,
        domains=[],
        sleep_substances=[],
        sleep_hours=None,
        wake_time=None,
        confidence=0.8,
        source=AnalysisSource.LOCAL,
        risk_level=RiskLevel.NONE,
        emotion_scores={"sadness": 0.8},
        model_id="local/model",
        model_revision="revision",
    )


def test_chatbot_uses_foundry_responses_without_provider_storage():
    responses = FakeResponses("Aku mendengarkan. Apa yang paling berat?")
    chatbot = FoundryChatbot(
        client=SimpleNamespace(responses=responses),
        deployment="gpt-chat",
        max_output_tokens=700,
    )

    reply = asyncio.run(
        chatbot.respond(
            language="id",
            checkin_mode="night",
            user_message="Aku sedih",
            analysis=analysis(),
            context={"recent_messages": [], "recent_recaps": [], "emotional_trends": {}},
        )
    )

    call = responses.calls[0]
    assert reply.startswith("Aku mendengarkan")
    assert call["model"] == "gpt-chat"
    assert call["store"] is False
    assert call["max_output_tokens"] == 700
    assert "jangan mendiagnosis" in call["instructions"].casefold()
    assert "jangan menyatakan hubungan sebab-akibat" in call["instructions"].casefold()
    assert "Aku sedih" in call["input"]


@pytest.mark.parametrize("output", [None, "", "   "])
def test_chatbot_rejects_empty_foundry_output(output):
    responses = FakeResponses(output)
    chatbot = FoundryChatbot(
        client=SimpleNamespace(responses=responses), deployment="gpt-chat"
    )

    with pytest.raises(FoundryChatError):
        asyncio.run(
            chatbot.respond(
                language="id",
                checkin_mode="night",
                user_message="Halo",
                analysis=analysis(),
                context={},
            )
        )

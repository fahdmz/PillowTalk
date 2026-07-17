import asyncio
import json
from types import SimpleNamespace

import pytest

from app.schemas.analysis import Domain, Emotion
from app.services.recap_generator import (
    FoundryRecapGenerator,
    RecapGenerationError,
)


class FakeResponses:
    def __init__(self, output_text):
        self.output_text = output_text
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=self.output_text)


def valid_output():
    return {
        "title": "Malam yang cukup berat",
        "summary": "Kamu membahas tekanan pekerjaan dan tidur yang lebih singkat.",
        "conclusion": "Malam ini terasa berat; istirahat perlahan bisa menjadi fokusmu.",
        "dominant_emotion": "sadness",
        "domains": ["work", "sleep"],
        "emotional_trend": {
            "direction": "stabil",
            "observation": "Kesedihan tampak konsisten selama percakapan.",
        },
        "sleep_observations": [
            "Pengguna melaporkan tidur sekitar lima jam.",
        ],
    }


def test_recap_generator_uses_strict_stateless_structured_output():
    responses = FakeResponses(json.dumps(valid_output()))
    generator = FoundryRecapGenerator(
        client=SimpleNamespace(responses=responses),
        deployment="gpt-recap",
        max_output_tokens=500,
    )

    recap = asyncio.run(
        generator.generate(
            checkin_mode="night",
            messages=[{"sender": "user", "text": "Aku sedih karena kerja."}],
            analyses=[{"emotion": "sadness", "domains": ["work"]}],
        )
    )

    call = responses.calls[0]
    assert recap.dominant_emotion is Emotion.SADNESS
    assert recap.domains == [Domain.WORK, Domain.SLEEP]
    assert call["model"] == "gpt-recap"
    assert call["store"] is False
    assert call["max_output_tokens"] == 500
    assert call["text"]["format"]["type"] == "json_schema"
    assert call["text"]["format"]["strict"] is True
    assert "Jangan mendiagnosis" in call["instructions"]
    assert "Aku sedih karena kerja." in call["input"]


@pytest.mark.parametrize(
    "output",
    [
        None,
        "",
        "not json",
        json.dumps({**valid_output(), "dominant_emotion": "anxious"}),
        json.dumps({**valid_output(), "unexpected": True}),
    ],
)
def test_recap_generator_rejects_empty_or_invalid_output(output):
    generator = FoundryRecapGenerator(
        client=SimpleNamespace(responses=FakeResponses(output)),
        deployment="gpt-recap",
    )

    with pytest.raises(RecapGenerationError):
        asyncio.run(
            generator.generate(
                checkin_mode="night",
                messages=[],
                analyses=[],
            )
        )

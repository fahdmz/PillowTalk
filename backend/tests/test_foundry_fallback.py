import asyncio
import importlib
import json
from types import SimpleNamespace
from typing import Any

import pytest

from app.schemas.analysis import ExtractedContext


def _foundry_module():
    try:
        return importlib.import_module("app.services.foundry_client")
    except ModuleNotFoundError:
        pytest.fail("app.services.foundry_client is not implemented")


def _fallback_module():
    try:
        return importlib.import_module("app.services.fallback_classifier")
    except ModuleNotFoundError:
        pytest.fail("app.services.fallback_classifier is not implemented")


class FakeResponses:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=self.output_text)


def test_builds_openai_v1_url_for_foundry_resource_endpoints() -> None:
    foundry = _foundry_module()

    assert foundry.build_foundry_base_url(
        "https://resource.services.ai.azure.com/"
    ) == "https://resource.services.ai.azure.com/openai/v1/"
    assert foundry.build_foundry_base_url(
        "https://resource.openai.azure.com/openai/v1"
    ) == "https://resource.openai.azure.com/openai/v1/"


def test_fallback_uses_strict_responses_schema_without_storage() -> None:
    fallback_module = _fallback_module()
    responses = FakeResponses(
        json.dumps(
            {
                "emotion": "surprise",
                "domains": ["sleep"],
                "sleep_substances": [],
                "sleep_hours": None,
                "wake_time": None,
                "confidence": 0.88,
            }
        )
    )
    client = SimpleNamespace(responses=responses)
    classifier = fallback_module.FoundryFallbackClassifier(
        client=client,
        deployment="gpt-5-mini-deployment",
    )

    result = asyncio.run(
        classifier.classify(
            "Kaget banget, aku cuma tidur 5 jam",
            ExtractedContext(domains=["sleep"], sleep_hours=5),
        )
    )

    request = responses.calls[0]
    assert request["model"] == "gpt-5-mini-deployment"
    assert request["store"] is False
    assert request["text"]["format"]["type"] == "json_schema"
    assert request["text"]["format"]["strict"] is True
    assert result.emotion.value == "surprise"
    assert result.sleep_hours == 5
    assert result.source.value == "foundry_fallback"


def test_fallback_rejects_malformed_model_output() -> None:
    fallback_module = _fallback_module()
    client = SimpleNamespace(responses=FakeResponses('{"emotion":"disgust"}'))
    classifier = fallback_module.FoundryFallbackClassifier(
        client=client,
        deployment="gpt-5-mini-deployment",
    )

    with pytest.raises(fallback_module.FoundryResponseError):
        asyncio.run(classifier.classify("Ambiguous", ExtractedContext()))

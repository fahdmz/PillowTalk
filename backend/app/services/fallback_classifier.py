"""Azure AI Foundry fallback for ambiguous local emotion classifications."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.schemas.analysis import (
    AnalysisResult,
    AnalysisSource,
    Domain,
    Emotion,
    ExtractedContext,
    RiskLevel,
    SleepSubstance,
)


SYSTEM_PROMPT = """You classify short PillowTalk messages written mainly in Indonesian,
possibly mixed with English. Return only the requested structured result. Choose exactly
one emotion. Add only clearly supported domains and sleep-related substances. Do not
invent sleep hours or wake times. Confidence describes confidence in the emotion label,
not the seriousness of the message."""


class FoundryResponseError(RuntimeError):
    """Raised when Foundry returns an unusable structured classification."""


class FoundryAnalysisOutput(BaseModel):
    """Strict output contract sent to Azure AI Foundry."""

    model_config = ConfigDict(extra="forbid")

    emotion: Emotion
    domains: list[Domain]
    sleep_substances: list[SleepSubstance]
    sleep_hours: float | None = Field(ge=0, le=24)
    wake_time: str | None
    confidence: float = Field(ge=0, le=1)

    @field_validator("wake_time")
    @classmethod
    def validate_wake_time(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            hour_text, minute_text = value.split(":", maxsplit=1)
            hour = int(hour_text)
            minute = int(minute_text)
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("wake_time must use HH:MM") from exc
        if len(value) != 5 or not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError("wake_time must use HH:MM")
        return value


class FoundryFallbackClassifier:
    """Classify uncertain messages with a strict Foundry Responses API schema."""

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

    async def classify(
        self,
        text: str,
        extracted: ExtractedContext,
    ) -> AnalysisResult:
        response = await self.client.responses.create(
            model=self.deployment,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "pillowtalk_message_analysis",
                    "strict": True,
                    "schema": FoundryAnalysisOutput.model_json_schema(),
                }
            },
            store=False,
            max_output_tokens=self.max_output_tokens,
            # Structured extraction against a fixed schema doesn't need
            # deep reasoning — and without capping it, gpt-5's default
            # reasoning effort can consume the whole max_output_tokens
            # budget before finishing (or even starting) the JSON body.
            reasoning={"effort": "minimal"},
        )

        try:
            parsed = FoundryAnalysisOutput.model_validate_json(response.output_text)
        except (AttributeError, TypeError, ValueError, ValidationError) as exc:
            raise FoundryResponseError(
                "Azure AI Foundry returned an invalid analysis response"
            ) from exc

        domains = _ordered_union(Domain, extracted.domains, parsed.domains)
        substances = _ordered_union(
            SleepSubstance,
            extracted.sleep_substances,
            parsed.sleep_substances,
        )

        return AnalysisResult(
            emotion=parsed.emotion,
            domains=domains,
            sleep_substances=substances,
            sleep_hours=(
                extracted.sleep_hours
                if extracted.sleep_hours is not None
                else parsed.sleep_hours
            ),
            wake_time=(
                extracted.wake_time
                if extracted.wake_time is not None
                else parsed.wake_time
            ),
            confidence=parsed.confidence,
            source=AnalysisSource.FOUNDRY_FALLBACK,
            risk_level=RiskLevel.NONE,
            emotion_scores={parsed.emotion.value: parsed.confidence},
            model_id=self.deployment,
            model_revision=None,
        )


def _ordered_union(enum_type: type, *values: list) -> list:
    selected = {item for group in values for item in group}
    return [item for item in enum_type if item in selected]

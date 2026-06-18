"""
Gemini Recommendation Service — Phase 7.

Uses the native google.genai SDK to call gemini-2.5-flash
for producing SRE-grade recommendations.
"""
from __future__ import annotations

import time
import logging
from datetime import datetime, timezone
from typing import Optional

from google import genai
from google.genai import types as genai_types

from config.settings import get_settings
from enums.recommendation_type import RecommendationType
from enums.recommendation_source import RecommendationSource
from enums.confidence_level import ConfidenceLevel
from schemas.recommendation_input import RecommendationInputSchema
from schemas.recommendation_output import RecommendationOutputState, CandidateRecommendation
from prompts.recommendation_prompt_builder import RecommendationPromptBuilder
from services.recommendation_response_validator import RecommendationResponseValidator
from utils.recommendation_logger import RecommendationLogger

logger = logging.getLogger(__name__)
rec_logger = RecommendationLogger("services.ai.gemini_recommendation_service")

_MODEL_NAME     = "gemini-2.5-flash"
_TEMPERATURE    = 0.2
_TOP_P          = 0.8
_TOP_K          = 20
_MAX_OUT_TOKENS = 700
_MAX_RETRIES    = 2

_FALLBACK_OUTPUT = RecommendationOutputState(
    recommendations=[RecommendationType.MONITOR_CLOSELY],
    reasoning=["Recommendation analysis unavailable due to Gemini API failure."],
    confidence=0,
    confidence_level=ConfidenceLevel.LOW,
    source=RecommendationSource.FALLBACK,
    model_name=_MODEL_NAME,
)


class GeminiRecommendationService:
    """
    Production-grade Gemini-powered Recommendation service.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.GOOGLE_API_KEY:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Cannot initialise GeminiRecommendationService."
            )
        self._client    = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self._builder   = RecommendationPromptBuilder()
        self._validator = RecommendationResponseValidator()
        logger.info("GeminiRecommendationService initialised with model %s.", _MODEL_NAME)

    def recommend(self, inp: RecommendationInputSchema) -> RecommendationOutputState:
        """
        Call Gemini to produce recommendations with retry logic.

        Args:
            inp: Validated input schema from CPUState.

        Returns:
            RecommendationOutputState — Gemini result or safe fallback.
        """
        rec_logger.log_input(
            inp.pod_name, inp.namespace,
            inp.root_cause_output.root_cause.value,
            inp.analyzer_output.severity.value
        )

        system_prompt, user_prompt = self._builder.build(inp)
        rec_logger.log_prompt(len(system_prompt), len(user_prompt))

        last_error: Optional[Exception] = None
        for attempt in range(1, _MAX_RETRIES + 2):
            try:
                start = time.monotonic()
                response = self._client.models.generate_content(
                    model=_MODEL_NAME,
                    contents=user_prompt,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=_TEMPERATURE,
                        top_p=_TOP_P,
                        top_k=_TOP_K,
                        max_output_tokens=_MAX_OUT_TOKENS,
                    ),
                )
                elapsed_ms = int((time.monotonic() - start) * 1000)

                raw_text = response.text or ""
                rec_logger.log_raw_response(raw_text)

                validated = self._validator.validate(raw_text)

                recs = [RecommendationType(r) for r in validated["recommendations"]]
                confidence = validated["confidence"]

                candidates = [
                    CandidateRecommendation(
                        recommendation=RecommendationType(c["recommendation"]),
                        confidence=int(c.get("confidence", 0)),
                        priority=c.get("priority", "MEDIUM"),
                        description=c.get("description", ""),
                    )
                    for c in validated.get("possible_recommendations", [])
                ]

                token_usage: Optional[int] = None
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    token_usage = getattr(response.usage_metadata, "total_token_count", None)

                output = RecommendationOutputState(
                    recommendations=recs,
                    reasoning=validated["reasoning"],
                    confidence=confidence,
                    confidence_level=ConfidenceLevel.from_score(confidence),
                    source=RecommendationSource.GEMINI,
                    possible_recommendations=candidates,
                    model_name=_MODEL_NAME,
                    execution_time_ms=elapsed_ms,
                    token_usage=token_usage,
                    timestamp=datetime.now(timezone.utc),
                )

                rec_logger.log_parsed_output(
                    [r.value for r in recs], confidence, output.source.value
                )
                rec_logger.log_execution_time("GeminiRecommendationService", elapsed_ms)
                return output

            except Exception as exc:
                last_error = exc
                if attempt <= _MAX_RETRIES:
                    rec_logger.log_retry(attempt, _MAX_RETRIES + 1, str(exc))
                else:
                    rec_logger.log_error("gemini_call", str(exc))
                    logger.error(
                        "GeminiRecommendationService: All %d attempts failed: %s",
                        _MAX_RETRIES + 1, exc, exc_info=True
                    )

        return _FALLBACK_OUTPUT

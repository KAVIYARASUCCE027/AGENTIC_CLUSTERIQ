"""
Gemini Root Cause Service — Phase 6.

Uses the native google.genai SDK (google-genai package) to call
gemini-2.5-flash for root cause analysis.

Responsibilities:
    - Build the prompt via RootCausePromptBuilder
    - Call Gemini with production-grade generation config
    - Validate the response via RootCauseResponseValidator
    - Return a fully-populated RootCauseOutputState
    - Leverage the existing retry_service for transient failures
"""
from __future__ import annotations

import time
import logging
from typing import Optional

from google import genai
from google.genai import types as genai_types

from config.settings import get_settings
from enums.root_cause_type import RootCauseType
from enums.root_cause_source import RootCauseSource
from schemas.root_cause_input import RootCauseInputSchema
from schemas.root_cause_output import RootCauseOutputState, CandidateCause
from prompts.root_cause_prompt_builder import RootCausePromptBuilder
from services.root_cause_response_validator import RootCauseResponseValidator
from utils.root_cause_logger import RootCauseLogger

logger = logging.getLogger(__name__)
rc_logger = RootCauseLogger("services.ai.gemini_root_cause_service")

_MODEL_NAME     = "gemini-2.5-flash"
_TEMPERATURE    = 0.1
_TOP_P          = 0.8
_TOP_K          = 20
_MAX_OUT_TOKENS = 500
_MAX_RETRIES    = 2


_FALLBACK_OUTPUT = RootCauseOutputState(
    root_cause=RootCauseType.UNKNOWN,
    confidence=0,
    evidence=["Root cause analysis unavailable due to Gemini API failure."],
    reasoning=["Gemini API call failed after retries."],
    possible_causes=[],
    source=RootCauseSource.FALLBACK,
    model_name=_MODEL_NAME,
)


class GeminiRootCauseService:
    """
    Production-grade Gemini-powered Root Cause Analysis service.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.GOOGLE_API_KEY:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Cannot initialise GeminiRootCauseService."
            )
        self._client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self._prompt_builder = RootCausePromptBuilder()
        self._validator = RootCauseResponseValidator()
        logger.info("GeminiRootCauseService initialised with model %s.", _MODEL_NAME)

    def analyze(self, inp: RootCauseInputSchema) -> RootCauseOutputState:
        """
        Run root cause analysis via Gemini with retry logic.

        Args:
            inp: Validated input schema built from CPUState.

        Returns:
            RootCauseOutputState — either Gemini result or safe fallback.
        """
        rc_logger.log_input(
            inp.pod_name, inp.namespace,
            inp.severity.value, inp.cpu_metrics.current_cpu_usage
        )

        system_prompt, user_prompt = self._prompt_builder.build(inp)
        rc_logger.log_prompt(len(system_prompt), len(user_prompt))

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
                rc_logger.log_raw_response(raw_text)

                validated = self._validator.validate(raw_text)

                # Build possible_causes list
                possible_causes = [
                    CandidateCause(
                        cause=RootCauseType(pc.get("cause", "UNKNOWN")),
                        confidence=int(pc.get("confidence", 0))
                    )
                    for pc in validated.get("possible_causes", [])
                    if pc.get("cause") in {rt.value for rt in RootCauseType}
                ]

                # Token usage — available via usage_metadata
                token_usage = None
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    token_usage = getattr(response.usage_metadata, "total_token_count", None)

                output = RootCauseOutputState(
                    root_cause=RootCauseType(validated["root_cause"]),
                    confidence=validated["confidence"],
                    evidence=validated["evidence"],
                    reasoning=validated["reasoning"],
                    possible_causes=possible_causes,
                    source=RootCauseSource.GEMINI,
                    model_name=_MODEL_NAME,
                    execution_time_ms=elapsed_ms,
                    token_usage=token_usage,
                )

                rc_logger.log_parsed_output(
                    output.root_cause.value, output.confidence, output.source.value
                )
                rc_logger.log_execution_time("GeminiRootCauseService", elapsed_ms)
                return output

            except Exception as exc:
                last_error = exc
                if attempt <= _MAX_RETRIES:
                    rc_logger.log_retry(attempt, _MAX_RETRIES + 1, str(exc))
                else:
                    rc_logger.log_error("gemini_call", str(exc))
                    logger.error(
                        "GeminiRootCauseService: All %d attempts failed. Last: %s",
                        _MAX_RETRIES + 1, exc, exc_info=True
                    )

        return _FALLBACK_OUTPUT

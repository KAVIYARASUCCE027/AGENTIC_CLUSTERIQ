"""
Gemini Action Planner Service — Phase 8.

Uses the native google.genai SDK to call gemini-2.5-flash
for producing an executable runbook of action steps.
"""
from __future__ import annotations

import time
import logging
from datetime import datetime, timezone
from typing import Optional

from google import genai
from google.genai import types as genai_types

from config.settings import get_settings
from enums.action_type import ActionType
from enums.action_priority import ActionPriority
from enums.action_risk import ActionRisk
from enums.action_source import ActionSource
from schemas.action_plan_input import ActionPlanInputSchema
from schemas.action_plan_output import ActionPlanOutputState, ActionStep
from prompts.action_planner_prompt_builder import ActionPlannerPromptBuilder
from services.action_plan_response_validator import ActionPlanResponseValidator
from utils.action_planner_logger import ActionPlannerLogger

logger = logging.getLogger(__name__)
plan_logger = ActionPlannerLogger("services.ai.gemini_action_planner_service")

_MODEL_NAME     = "gemini-2.5-flash"
_TEMPERATURE    = 0.1
_TOP_P          = 0.8
_TOP_K          = 20
_MAX_OUT_TOKENS = 1000
_MAX_RETRIES    = 2

_FALLBACK_OUTPUT = ActionPlanOutputState(
    actions=[
        ActionStep(
            step=1,
            action="Monitor system closely; AI plan generation failed.",
            action_type=ActionType.NO_ACTION,
            risk=ActionRisk.LOW,
            estimated_duration="Ongoing"
        )
    ],
    priority=ActionPriority.LOW,
    risk=ActionRisk.LOW,
    estimated_duration="Unknown",
    rollback_strategy="N/A",
    confidence=0,
    source=ActionSource.FALLBACK,
    model_name=_MODEL_NAME,
)


class GeminiActionPlannerService:
    """
    Production-grade Gemini-powered Action Planner service.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.GOOGLE_API_KEY:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Cannot initialise GeminiActionPlannerService."
            )
        self._client    = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self._builder   = ActionPlannerPromptBuilder()
        self._validator = ActionPlanResponseValidator()
        logger.info("GeminiActionPlannerService initialised with model %s.", _MODEL_NAME)

    def plan_action(self, inp: ActionPlanInputSchema) -> ActionPlanOutputState:
        """
        Call Gemini to produce an action plan with retry logic.
        """
        recs = [r.value for r in inp.recommendation_output.recommendations]
        plan_logger.log_input(inp.pod_name, inp.namespace, recs)

        system_prompt, user_prompt = self._builder.build(inp)
        plan_logger.log_prompt(len(system_prompt), len(user_prompt))

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
                plan_logger.log_raw_response(raw_text)

                validated = self._validator.validate(raw_text)

                action_steps = [
                    ActionStep(
                        step=act["step"],
                        action=act["action"],
                        action_type=ActionType(act["action_type"]),
                        risk=ActionRisk(act["risk"]),
                        estimated_duration=act["estimated_duration"]
                    )
                    for act in validated["actions"]
                ]

                token_usage: Optional[int] = None
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    token_usage = getattr(response.usage_metadata, "total_token_count", None)

                output = ActionPlanOutputState(
                    actions=action_steps,
                    priority=ActionPriority(validated["priority"]),
                    risk=ActionRisk(validated["risk"]),
                    estimated_duration=validated.get("estimated_duration", "Unknown"),
                    rollback_strategy=validated.get("rollback_strategy", "None"),
                    confidence=validated["confidence"],
                    source=ActionSource.GEMINI,
                    model_name=_MODEL_NAME,
                    execution_time_ms=elapsed_ms,
                    token_usage=token_usage,
                    timestamp=datetime.now(timezone.utc),
                )

                plan_logger.log_parsed_output(
                    len(action_steps), output.confidence, output.source.value
                )
                plan_logger.log_execution_time("GeminiActionPlannerService", elapsed_ms)
                return output

            except Exception as exc:
                last_error = exc
                if attempt <= _MAX_RETRIES:
                    plan_logger.log_retry(attempt, _MAX_RETRIES + 1, str(exc))
                else:
                    plan_logger.log_error("gemini_call", str(exc))
                    logger.error(
                        "GeminiActionPlannerService: All %d attempts failed: %s",
                        _MAX_RETRIES + 1, exc, exc_info=True
                    )

        return _FALLBACK_OUTPUT

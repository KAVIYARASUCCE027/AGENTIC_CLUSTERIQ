"""
Action Planner Output Schema — Phase 8.

Validated output from either GeminiActionPlannerService
or FallbackActionPlannerService.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

from enums.action_type import ActionType
from enums.action_priority import ActionPriority
from enums.action_risk import ActionRisk
from enums.action_source import ActionSource


class ActionStep(BaseModel):
    """A single step in the action plan."""
    step: int = Field(ge=1)
    action: str = Field(min_length=1)
    action_type: ActionType = Field(default=ActionType.NO_ACTION)
    risk: ActionRisk = Field(default=ActionRisk.LOW)
    estimated_duration: str = Field(default="Unknown")


class ActionPlanOutputState(BaseModel):
    """
    Structured output from the Action Planner Agent.

    Fields:
        actions              — Ordered list of action steps.
        priority             — Overall priority of the plan.
        risk                 — Overall risk of the plan.
        estimated_duration   — Total estimated duration.
        rollback_strategy    — Steps to revert the actions.
        confidence           — Overall confidence in the plan (0–100).
        source               — GEMINI or FALLBACK.
        model_name           — Model used (or "fallback").
        execution_time_ms    — Wall-clock time for the AI call.
        token_usage          — Gemini token count (if available).
        timestamp            — UTC timestamp of analysis.
    """
    actions: List[ActionStep] = Field(default_factory=list)
    priority: ActionPriority = Field(default=ActionPriority.LOW)
    risk: ActionRisk = Field(default=ActionRisk.LOW)
    estimated_duration: str = Field(default="0 minutes")
    rollback_strategy: str = Field(default="No rollback defined.")
    confidence: int = Field(default=0, ge=0, le=100)
    source: ActionSource = Field(default=ActionSource.FALLBACK)
    model_name: str = Field(default="fallback")
    execution_time_ms: int = Field(default=0, ge=0)
    token_usage: Optional[int] = Field(default=None)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Config:
        json_schema_extra = {
            "title": "ActionPlanOutputState",
            "description": "Validated action plan from AI or deterministic fallback.",
        }

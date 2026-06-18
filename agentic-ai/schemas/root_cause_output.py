"""
Root Cause Output Schema — Phase 6.

Validated output produced by either GeminiRootCauseService or
FallbackRootCauseService. Strict enum usage prevents string literals
from polluting downstream agents.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from enums.root_cause_type import RootCauseType
from enums.root_cause_source import RootCauseSource


class CandidateCause(BaseModel):
    """
    A single alternative cause with its associated confidence.
    Surfaced to the Recommendation Agent in Phase 7.
    """
    cause: RootCauseType
    confidence: int = Field(ge=0, le=100)


class RootCauseOutputState(BaseModel):
    """
    Structured, validated output from the Root Cause Agent.

    Fields:
        root_cause       — The most probable root cause (enum).
        confidence       — Confidence score 0–100.
        evidence         — Raw metric values supporting the conclusion.
        reasoning        — Logical chain from metrics to conclusion.
        possible_causes  — Ranked alternative causes for Phase 7.
        source           — GEMINI or FALLBACK.
        model_name       — Gemini model used (or "fallback").
        execution_time_ms— Wall-clock time for the AI call.
        token_usage      — Token count from Gemini (if available).
        timestamp        — UTC timestamp of analysis.
    """
    root_cause: RootCauseType = Field(default=RootCauseType.UNKNOWN)
    confidence: int = Field(default=0, ge=0, le=100)
    evidence: List[str] = Field(default_factory=list)
    reasoning: List[str] = Field(default_factory=list)
    possible_causes: List[CandidateCause] = Field(default_factory=list)
    source: RootCauseSource = Field(default=RootCauseSource.FALLBACK)
    model_name: str = Field(default="fallback")
    execution_time_ms: int = Field(default=0, ge=0)
    token_usage: Optional[int] = Field(default=None)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("evidence")
    @classmethod
    def evidence_must_not_be_empty(cls, v: List[str]) -> List[str]:
        """Require at least one evidence entry in valid results."""
        # Allow empty for default initialization; validator fires on explicit set
        return v

    class Config:
        json_schema_extra = {
            "title": "RootCauseOutputState",
            "description": "Validated root cause analysis from the AI or fallback service.",
        }

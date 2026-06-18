"""
Recommendation Output Schema — Phase 7.

Validated output from either GeminiRecommendationService
or FallbackRecommendationService.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

from enums.recommendation_type import RecommendationType
from enums.recommendation_source import RecommendationSource
from enums.confidence_level import ConfidenceLevel


class Priority(str):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"


class CandidateRecommendation(BaseModel):
    """A single recommendation with confidence and priority."""
    recommendation: RecommendationType
    confidence: int = Field(ge=0, le=100)
    priority: str = Field(default="MEDIUM")
    description: str = Field(default="")


class RecommendationOutputState(BaseModel):
    """
    Structured output from the Recommendation Agent.

    Fields:
        recommendations      — Ordered list of RecommendationType enum values.
        reasoning            — Logical chain explaining why each action is needed.
        confidence           — Overall confidence in the recommendations (0–100).
        confidence_level     — Human-readable confidence band.
        source               — GEMINI or FALLBACK.
        possible_recommendations — Ranked alternatives for Phase 8.
        model_name           — Model used (or "fallback").
        execution_time_ms    — Wall-clock time for the AI call.
        token_usage          — Gemini token count (if available).
        timestamp            — UTC timestamp of analysis.
    """
    recommendations: List[RecommendationType] = Field(default_factory=list)
    reasoning: List[str] = Field(default_factory=list)
    confidence: int = Field(default=0, ge=0, le=100)
    confidence_level: ConfidenceLevel = Field(default=ConfidenceLevel.LOW)
    source: RecommendationSource = Field(default=RecommendationSource.FALLBACK)
    possible_recommendations: List[CandidateRecommendation] = Field(default_factory=list)
    model_name: str = Field(default="fallback")
    execution_time_ms: int = Field(default=0, ge=0)
    token_usage: Optional[int] = Field(default=None)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Config:
        json_schema_extra = {
            "title": "RecommendationOutputState",
            "description": "Validated recommendation output from AI or deterministic fallback.",
        }

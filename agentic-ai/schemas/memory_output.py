"""
Memory Output Schema — Phase 9.

Represents the retrieved historical context for an incident.
Used by the Memory Node to populate CPUState.memory_output.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from enums.memory_source import MemorySource
from schemas.memory.incident_record import IncidentRecord


class SimilarIncident(BaseModel):
    """A historical incident matched by the Similarity Engine."""
    incident_id: str
    pod_name: str
    timestamp: str
    root_cause: str
    severity: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    resolution_status: str


class HistoricalPattern(BaseModel):
    """A pattern identified across multiple historical incidents."""
    pattern_type: str
    frequency: int
    description: str


class MemorySummary(BaseModel):
    """Human-readable context generated for downstream agents."""
    context: str
    key_takeaways: List[str]


class MemoryOutputState(BaseModel):
    """
    Structured output from the Memory Agent.

    Fields:
        similar_incidents    — List of past incidents matching current signature.
        historical_patterns  — Aggregated patterns (e.g. repeated OOMs on pod).
        memory_summary       — Text context for AI consumption.
        incident_count       — Total related incidents analyzed.
        source               — MONGODB, IN_MEMORY, or FALLBACK.
    """
    similar_incidents: List[SimilarIncident] = Field(default_factory=list)
    historical_patterns: List[HistoricalPattern] = Field(default_factory=list)
    memory_summary: MemorySummary = Field(
        default_factory=lambda: MemorySummary(context="No history available.", key_takeaways=[])
    )
    incident_count: int = Field(default=0, ge=0)
    source: MemorySource = Field(default=MemorySource.FALLBACK)

    class Config:
        json_schema_extra = {
            "title": "MemoryOutputState",
            "description": "Historical context retrieved from the Memory Layer.",
        }

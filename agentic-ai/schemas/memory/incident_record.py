"""
Incident Record Schema — Phase 9.

Represents a full incident stored in MongoDB.
Aggregates all snapshots from the pipeline phases into a single
historical record for future AI retrieval.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

from enums.incident_status import IncidentStatus
from enums.root_cause_type import RootCauseType
from enums.recommendation_type import RecommendationType
from enums.action_type import ActionType
from schemas.analyzer_output import HealthStatus, Severity, AbnormalityType


class MetricsSnapshot(BaseModel):
    cpu_usage: float
    avg_cpu_5m: float
    avg_cpu_15m: float
    cpu_trend: str
    cpu_limit: float
    cpu_request: float
    restart_count: int
    replica_count: int


class AnalyzerSnapshot(BaseModel):
    health_status: HealthStatus
    severity: Severity
    abnormality: AbnormalityType
    confidence: int


class RootCauseSnapshot(BaseModel):
    root_cause: RootCauseType
    confidence: int
    evidence: List[str]


class RecommendationSnapshot(BaseModel):
    recommendations: List[RecommendationType]
    confidence: int


class ActionPlanSnapshot(BaseModel):
    action_types: List[ActionType]
    priority: str
    risk: str
    confidence: int


class IncidentRecord(BaseModel):
    """
    Strongly typed representation of a MongoDB `cpu_incidents` document.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    
    pod_name: str
    namespace: str
    status: IncidentStatus = Field(default=IncidentStatus.OPEN)
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    metrics: MetricsSnapshot
    analyzer: AnalyzerSnapshot
    root_cause: RootCauseSnapshot
    recommendation: RecommendationSnapshot
    action_plan: ActionPlanSnapshot

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "title": "IncidentRecord",
            "description": "Historical incident stored in MongoDB.",
        }

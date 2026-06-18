"""
Root Cause Input Schema — Phase 6.

Structured input for the Root Cause Agent. Bridges CPUState
to the Gemini service in a clean, validated form.
"""
from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field

from schemas.analyzer_output import Severity, AbnormalityType


class CPUMetricsInput(BaseModel):
    current_cpu_usage: float = Field(description="Current CPU usage %.")
    avg_cpu_5m: float = Field(description="5-minute average CPU %.")
    avg_cpu_15m: float = Field(description="15-minute average CPU %.")
    cpu_trend: str = Field(description="INCREASING, STABLE, or DECREASING.")
    throttling_percentage: float = Field(default=0.0)
    cpu_limit: float = Field(default=0.0, description="Configured CPU limit (millicores).")
    cpu_request: float = Field(default=0.0, description="Configured CPU request (millicores).")


class RestartMetricsInput(BaseModel):
    restart_count: int = Field(description="Total container restart count.")


class ReplicaMetricsInput(BaseModel):
    current_replicas: int = Field(description="Current running replica count.")


class RootCauseInputSchema(BaseModel):
    """
    Validated input contract for the Root Cause Agent.
    Built by root_cause_node from the live CPUState.
    """
    pod_name: str
    namespace: str
    severity: Severity
    abnormality: AbnormalityType
    analyzer_reasoning: List[str] = Field(
        default_factory=list,
        description="Reasoning strings produced by the Phase 5 Analyzer Node.",
    )
    cpu_metrics: CPUMetricsInput
    restart_metrics: RestartMetricsInput
    replica_metrics: ReplicaMetricsInput

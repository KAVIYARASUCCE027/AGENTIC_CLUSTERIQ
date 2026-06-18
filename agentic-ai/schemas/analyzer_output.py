from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class HealthStatus(str, Enum):
    NORMAL = "NORMAL"
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AbnormalityType(str, Enum):
    NONE = "NONE"
    CPU_SPIKE = "CPU_SPIKE"
    SUSTAINED_HIGH_CPU = "SUSTAINED_HIGH_CPU"
    THROTTLING_RISK = "THROTTLING_RISK"
    NODE_RESOURCE_CONTENTION = "NODE_RESOURCE_CONTENTION"
    INSUFFICIENT_REPLICAS = "INSUFFICIENT_REPLICAS"

class AnalyzerOutputState(BaseModel):
    """
    Structured output from the deterministic Analyzer Node.
    """
    health_status: HealthStatus = Field(default=HealthStatus.NORMAL)
    severity: Severity = Field(default=Severity.LOW)
    abnormality: AbnormalityType = Field(default=AbnormalityType.NONE)
    root_cause: str = Field(default="")
    trend: str = Field(default="STABLE")
    confidence: int = Field(default=0, ge=0, le=100)
    reasoning: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    action_plan: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "title": "AnalyzerOutputState",
            "description": "Deterministic rule-based analysis and recommendations.",
        }

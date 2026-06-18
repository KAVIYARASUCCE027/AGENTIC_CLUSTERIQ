from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field

class CPUIncident(BaseModel):
    """Represents a CPU incident triggered by a metric node."""
    incident_id: str = Field(default_factory=lambda: str(uuid4()))
    pod_name: str
    namespace: str = "default"
    cpu_usage: float
    cpu_limit: float
    severity: str
    incident_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

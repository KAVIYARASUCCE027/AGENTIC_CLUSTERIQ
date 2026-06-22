from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from schemas.enums.incident_status import IncidentStatus
from schemas.enums.incident_severity import IncidentSeverity

class IncidentSchema(BaseModel):
    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.OPEN
    root_cause: Optional[str] = None
    recommendation: Optional[str] = None
    pod_name: str
    namespace: str
    resource_type: str = "COMPOSITE"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    related_events: List[str] = Field(default_factory=list)

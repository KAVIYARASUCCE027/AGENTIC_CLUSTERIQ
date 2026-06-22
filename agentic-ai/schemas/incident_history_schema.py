from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from schemas.enums.incident_status import IncidentStatus
from schemas.enums.incident_severity import IncidentSeverity

class IncidentHistorySchema(BaseModel):
    incident_id: str
    previous_status: Optional[IncidentStatus] = None
    new_status: IncidentStatus
    previous_severity: Optional[IncidentSeverity] = None
    new_severity: IncidentSeverity
    changed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    changed_by: str = "SYSTEM"

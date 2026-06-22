from pydantic import BaseModel
from schemas.enums.incident_status import IncidentStatus
from schemas.enums.incident_severity import IncidentSeverity

class IncidentOutput(BaseModel):
    incident_id: str
    incident_status: IncidentStatus
    incident_severity: IncidentSeverity

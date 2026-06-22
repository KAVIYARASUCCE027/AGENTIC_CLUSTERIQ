from pydantic import BaseModel
from typing import List
from schemas.incident_schema import IncidentSchema
from schemas.incident_history_schema import IncidentHistorySchema

class IncidentResponse(BaseModel):
    incident: IncidentSchema
    history: List[IncidentHistorySchema] = []

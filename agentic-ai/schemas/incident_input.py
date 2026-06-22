from pydantic import BaseModel
from typing import Optional, List

class IncidentInput(BaseModel):
    pod_name: str
    namespace: str
    related_events: List[str] = []
    root_cause: Optional[str] = None
    recommendation: Optional[str] = None

import logging
from typing import List, Optional
from database.mongo_client import get_db
from schemas.incident_schema import IncidentSchema
from schemas.incident_history_schema import IncidentHistorySchema
from schemas.enums.incident_status import IncidentStatus
from schemas.enums.incident_severity import IncidentSeverity
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class IncidentRepository:
    def __init__(self):
        self._db = get_db()
        self._incidents = self._db["incidents"]
        self._history = self._db["incident_history"]

    def save_incident(self, incident: IncidentSchema) -> IncidentSchema:
        doc = incident.model_dump()
        self._incidents.update_one(
            {"incident_id": incident.incident_id},
            {"$set": doc},
            upsert=True
        )
        return incident

    def find_by_id(self, incident_id: str) -> Optional[IncidentSchema]:
        doc = self._incidents.find_one({"incident_id": incident_id})
        if doc:
            doc.pop("_id", None)
            return IncidentSchema(**doc)
        return None

    def find_open_incidents(self) -> List[IncidentSchema]:
        docs = self._incidents.find({"status": IncidentStatus.OPEN.value})
        results = []
        for doc in docs:
            doc.pop("_id", None)
            results.append(IncidentSchema(**doc))
        return results

    def find_resolved_incidents(self) -> List[IncidentSchema]:
        docs = self._incidents.find({"status": IncidentStatus.RESOLVED.value})
        results = []
        for doc in docs:
            doc.pop("_id", None)
            results.append(IncidentSchema(**doc))
        return results

    def update_status(self, incident_id: str, status: IncidentStatus) -> bool:
        result = self._incidents.update_one(
            {"incident_id": incident_id},
            {"$set": {
                "status": status.value,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        return result.modified_count > 0

    def update_severity(self, incident_id: str, severity: IncidentSeverity) -> bool:
        result = self._incidents.update_one(
            {"incident_id": incident_id},
            {"$set": {
                "severity": severity.value,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        return result.modified_count > 0

    def save_history(self, history: IncidentHistorySchema) -> IncidentHistorySchema:
        doc = history.model_dump()
        self._history.insert_one(doc)
        return history

    def find_history(self, incident_id: str) -> List[IncidentHistorySchema]:
        docs = self._history.find({"incident_id": incident_id}).sort("changed_at", 1)
        results = []
        for doc in docs:
            doc.pop("_id", None)
            results.append(IncidentHistorySchema(**doc))
        return results

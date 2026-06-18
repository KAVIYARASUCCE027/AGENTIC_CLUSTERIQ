"""
Incident Repository — Phase 9.

CRUD operations for the cpu_incidents collection.
"""
from typing import Optional, List, Dict, Any
from pymongo import DESCENDING

from database.collections import get_cpu_incidents_collection
from schemas.memory.incident_record import IncidentRecord


class IncidentRepository:
    def __init__(self):
        self._col = get_cpu_incidents_collection()

    def save(self, record: IncidentRecord) -> str:
        """Insert a new incident record."""
        doc = record.model_dump(by_alias=True)
        # Ensure enums are converted to strings if pydantic didn't fully handle it,
        # but model_dump(mode='json') or just model_dump usually does fine for basic enums.
        # Let's use mode='json' to be safe with datetime and enums.
        doc_json = record.model_dump(mode="json", by_alias=True)
        self._col.insert_one(doc_json)
        return doc_json["_id"]

    def find_by_id(self, incident_id: str) -> Optional[IncidentRecord]:
        """Find a record by its business ID."""
        doc = self._col.find_one({"incident_id": incident_id})
        if doc:
            return IncidentRecord(**doc)
        return None

    def list_recent(self, limit: int = 10) -> List[IncidentRecord]:
        """List the most recent incidents globally."""
        cursor = self._col.find().sort("timestamp", DESCENDING).limit(limit)
        return [IncidentRecord(**doc) for doc in cursor]

    def archive(self, incident_id: str) -> bool:
        """Mark an incident as archived."""
        result = self._col.update_one(
            {"incident_id": incident_id},
            {"$set": {"status": "ARCHIVED"}}
        )
        return result.modified_count > 0

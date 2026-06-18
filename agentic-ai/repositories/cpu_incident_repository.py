from typing import Optional, List, Dict, Any
from database.collections import get_cpu_incidents_collection
from models.cpu_incident import CPUIncident

class CPUIncidentRepository:
    """Repository for CPUIncident data access."""
    
    def __init__(self):
        self.collection = get_cpu_incidents_collection()

    def create(self, incident: CPUIncident) -> str:
        """Create a new CPU incident document."""
        doc = incident.model_dump()
        self.collection.insert_one(doc)
        return incident.incident_id

    def get_by_id(self, incident_id: str) -> Optional[CPUIncident]:
        """Retrieve a CPU incident by its ID."""
        doc = self.collection.find_one({"incident_id": incident_id})
        if doc:
            return CPUIncident(**doc)
        return None

    def update_status(self, incident_id: str, resolved: bool) -> bool:
        """Update the resolved status of an incident."""
        result = self.collection.update_one(
            {"incident_id": incident_id},
            {"$set": {"resolved": resolved}}
        )
        return result.modified_count > 0

    def find_recent_unresolved(self, limit: int = 10) -> List[CPUIncident]:
        """Find recent unresolved CPU incidents."""
        cursor = self.collection.find({"resolved": False}).sort("incident_time", -1).limit(limit)
        return [CPUIncident(**doc) for doc in cursor]

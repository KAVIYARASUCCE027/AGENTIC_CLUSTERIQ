from typing import Optional, List
from database.collections import get_resolution_history_collection
from models.resolution_history import ResolutionHistory

class ResolutionRepository:
    """Repository for ResolutionHistory data access."""
    
    def __init__(self):
        self.collection = get_resolution_history_collection()

    def create(self, resolution: ResolutionHistory) -> str:
        """Create a new resolution history document."""
        doc = resolution.model_dump()
        self.collection.insert_one(doc)
        return resolution.resolution_id

    def get_by_id(self, resolution_id: str) -> Optional[ResolutionHistory]:
        """Retrieve resolution history by ID."""
        doc = self.collection.find_one({"resolution_id": resolution_id})
        if doc:
            return ResolutionHistory(**doc)
        return None

    def get_by_incident_id(self, incident_id: str) -> List[ResolutionHistory]:
        """Retrieve resolution history for a specific incident."""
        cursor = self.collection.find({"incident_id": incident_id})
        return [ResolutionHistory(**doc) for doc in cursor]

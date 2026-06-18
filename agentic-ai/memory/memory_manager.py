import logging
from typing import Dict, Any, List
from repositories.memory_repository import MemoryRepository

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Manages complex memory retrieval tasks, orchestrating data fetches
    across different repositories (incidents, resolutions, actions).
    """
    
    def __init__(self):
        self.repository = MemoryRepository()

    def get_full_context_for_incidents(self, incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich a list of incidents with their associated resolutions and actions.
        """
        enriched_incidents = []
        for incident in incidents:
            incident_id = incident.get("incident_id")
            if not incident_id:
                continue
                
            resolutions = self.repository.get_resolution_for_incident(incident_id)
            actions = self.repository.get_actions_for_incident(incident_id)
            
            # Create an enriched document
            enriched = incident.copy()
            enriched["resolutions"] = resolutions
            enriched["actions"] = actions
            enriched_incidents.append(enriched)
            
        return enriched_incidents

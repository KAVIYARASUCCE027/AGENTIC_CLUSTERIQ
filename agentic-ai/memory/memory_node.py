import logging
from typing import Dict, Any, List
from memory.similarity_search import SimilaritySearch
from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class MemoryNode:
    """
    Node in the agent graph responsible for fetching relevant historical data
    and injecting it into the state before analysis.
    """
    
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.similarity_search = SimilaritySearch(self.memory_manager)

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state, find similar past incidents, 
        and attach them to the state under 'previous_incidents'.
        """
        logger.info("MemoryNode processing state...")
        
        # Determine the key to search by, e.g. pod_name or incident type
        search_criteria = {}
        if "pod_name" in state:
            search_criteria["pod_name"] = state["pod_name"]
            
        if not search_criteria:
            logger.warning("No search criteria found in state for memory retrieval.")
            state["previous_incidents"] = []
            return state

        # Retrieve similar incidents
        similar_incidents = self.similarity_search.find_similar(search_criteria)
        
        # Retrieve full context (resolutions, actions) for these incidents
        contextualized_incidents = self.memory_manager.get_full_context_for_incidents(similar_incidents)
        
        state["previous_incidents"] = contextualized_incidents
        logger.info(f"MemoryNode injected {len(contextualized_incidents)} past incidents into state.")
        return state

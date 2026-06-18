import logging
from typing import Dict, Any, List
from repositories.memory_repository import MemoryRepository

logger = logging.getLogger(__name__)

class SimilaritySearch:
    """
    Performs similarity matching against past incidents to find relevant historical context.
    """
    
    def __init__(self, memory_manager=None):
        self.repository = MemoryRepository()
        self.memory_manager = memory_manager

    def find_similar(self, query: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find past incidents that match the query criteria.
        In the future, this can be expanded to use vector embeddings and cosine similarity.
        For now, it performs an exact match or simple filtering.
        """
        logger.debug(f"Performing similarity search with query: {query}")
        
        # Simple exact match against DB
        # E.g. {"pod_name": "frontend-pod", "resolved": True}
        results = self.repository.get_past_incidents(query, limit)
        
        return results

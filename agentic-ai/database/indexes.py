"""
MongoDB Index Initialisation — Phase 9.

Ensures performance-critical indexes exist.
"""
import logging
from pymongo import ASCENDING, DESCENDING

from database.collections import get_cpu_incidents_collection

logger = logging.getLogger(__name__)

def ensure_indexes() -> None:
    """Create indexes for memory retrieval."""
    try:
        col = get_cpu_incidents_collection()
        
        # Fast retrieval by pod
        col.create_index([("pod_name", ASCENDING), ("namespace", ASCENDING)])
        
        # Fast retrieval by time
        col.create_index([("timestamp", DESCENDING)])
        
        # Similarity search indexes
        col.create_index([("root_cause.root_cause", ASCENDING)])
        col.create_index([("analyzer.severity", ASCENDING)])
        
        logger.info("MongoDB indexes verified successfully.")
    except Exception as e:
        logger.warning(f"Failed to create MongoDB indexes: {e}")

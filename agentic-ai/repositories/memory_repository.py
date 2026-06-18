"""
Memory Repository — Phase 9.

Advanced queries (similarity, patterns) for the cpu_incidents collection.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

from database.collections import get_cpu_incidents_collection


class MemoryRepository:
    def __init__(self):
        self._col = get_cpu_incidents_collection()

    def find_similar(self, pod_name: str, namespace: str, root_cause: str, severity: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find recent similar incidents based on pod, root cause, and severity.
        Since we don't have a vector store yet (Phase 10), we use deterministic matching
        with an aggregation pipeline to score results.
        """
        pipeline = [
            # 1. Match candidates (same pod OR same root_cause) within the last 90 days
            {
                "$match": {
                    "$or": [
                        {"pod_name": pod_name, "namespace": namespace},
                        {"root_cause.root_cause": root_cause}
                    ],
                    "timestamp": {"$gte": (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()}
                }
            },
            # 2. Add similarity score field
            {
                "$addFields": {
                    "similarity_score": {
                        "$sum": [
                            {"$cond": [{"$and": [{"$eq": ["$pod_name", pod_name]}, {"$eq": ["$namespace", namespace]}]}, 0.4, 0.0]},
                            {"$cond": [{"$eq": ["$root_cause.root_cause", root_cause]}, 0.4, 0.0]},
                            {"$cond": [{"$eq": ["$analyzer.severity", severity]}, 0.2, 0.0]}
                        ]
                    }
                }
            },
            # 3. Filter out weak matches
            {
                "$match": {
                    "similarity_score": {"$gte": 0.4}
                }
            },
            # 4. Sort by score (desc) and timestamp (desc)
            {
                "$sort": {"similarity_score": -1, "timestamp": -1}
            },
            # 5. Limit results
            {"$limit": limit}
        ]
        
        return list(self._col.aggregate(pipeline))

    def extract_patterns(self, pod_name: str, namespace: str) -> List[Dict[str, Any]]:
        """
        Aggregate incidents for a pod to find recurring root causes.
        """
        pipeline = [
            {
                "$match": {
                    "pod_name": pod_name,
                    "namespace": namespace,
                    "timestamp": {"$gte": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()}
                }
            },
            {
                "$group": {
                    "_id": "$root_cause.root_cause",
                    "count": {"$sum": 1}
                }
            },
            {
                "$match": {
                    "count": {"$gt": 1}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]
        
        return list(self._col.aggregate(pipeline))

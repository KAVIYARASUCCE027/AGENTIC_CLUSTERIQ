from typing import Optional, List
from database.collections import get_execution_history_collection
from models.execution_history import AgentExecutionHistory

class ExecutionRepository:
    """Repository for AgentExecutionHistory data access."""
    
    def __init__(self):
        self.collection = get_execution_history_collection()

    def create(self, execution: AgentExecutionHistory) -> str:
        """Create a new execution history document."""
        doc = execution.model_dump()
        self.collection.insert_one(doc)
        return execution.execution_id

    def get_by_id(self, execution_id: str) -> Optional[AgentExecutionHistory]:
        """Retrieve execution history by ID."""
        doc = self.collection.find_one({"execution_id": execution_id})
        if doc:
            return AgentExecutionHistory(**doc)
        return None

    def get_by_incident_id(self, incident_id: str) -> List[AgentExecutionHistory]:
        """Retrieve execution history for a specific incident."""
        cursor = self.collection.find({"incident_id": incident_id}).sort("start_time", -1)
        return [AgentExecutionHistory(**doc) for doc in cursor]

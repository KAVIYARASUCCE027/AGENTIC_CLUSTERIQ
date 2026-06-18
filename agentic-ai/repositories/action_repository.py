from typing import Optional, List
from database.collections import get_action_history_collection
from models.action_history import ActionHistory

class ActionRepository:
    """Repository for ActionHistory data access."""
    
    def __init__(self):
        self.collection = get_action_history_collection()

    def create(self, action: ActionHistory) -> str:
        """Create a new action history document."""
        doc = action.model_dump()
        self.collection.insert_one(doc)
        return action.action_id

    def get_by_id(self, action_id: str) -> Optional[ActionHistory]:
        """Retrieve action history by ID."""
        doc = self.collection.find_one({"action_id": action_id})
        if doc:
            return ActionHistory(**doc)
        return None

    def get_by_execution_id(self, execution_id: str) -> List[ActionHistory]:
        """Retrieve action history for a specific execution."""
        cursor = self.collection.find({"execution_id": execution_id})
        return [ActionHistory(**doc) for doc in cursor]

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field

class ActionHistory(BaseModel):
    """Represents an action taken by an agent."""
    action_id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: Optional[str] = None
    execution_id: str
    action_type: str
    action_details: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

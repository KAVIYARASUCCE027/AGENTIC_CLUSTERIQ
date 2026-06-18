from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import uuid4
from pydantic import BaseModel, Field

class AgentExecutionHistory(BaseModel):
    """Represents the execution history of an agent."""
    execution_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str
    incident_id: Optional[str] = None
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    status: str = "running"
    state: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

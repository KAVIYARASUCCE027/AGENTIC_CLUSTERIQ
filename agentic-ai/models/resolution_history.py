from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field

class ResolutionHistory(BaseModel):
    """Represents a resolution attempt for an incident."""
    resolution_id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    execution_id: Optional[str] = None
    strategy_used: str
    successful: bool
    details: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

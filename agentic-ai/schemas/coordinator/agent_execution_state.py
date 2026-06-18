"""
Agent Execution State — Phase 10.
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class AgentStatus(str, Enum):
    PENDING   = "PENDING"
    RUNNING   = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED    = "FAILED"
    SKIPPED   = "SKIPPED"


class AgentExecutionState(BaseModel):
    agent_name: str
    status: AgentStatus = Field(default=AgentStatus.PENDING)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: int = 0
    retry_count: int = 0
    token_usage: int = 0
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_schema_extra = {
            "title": "AgentExecutionState",
            "description": "Tracks the execution metadata of an individual agent.",
        }

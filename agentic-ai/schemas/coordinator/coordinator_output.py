"""
Coordinator Output Schema — Phase 10.
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from schemas.cpu_state import CPUState
from schemas.coordinator.agent_execution_state import AgentExecutionState

class CoordinatorOutput(BaseModel):
    final_state: CPUState
    execution_summary: str
    total_latency_ms: int
    agent_execution_states: List[AgentExecutionState] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "title": "CoordinatorOutput",
            "description": "Output payload from the MultiAgentCoordinator.",
        }

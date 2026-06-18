"""
Coordinator Input Schema — Phase 10.
"""
from pydantic import BaseModel, Field
from schemas.cpu_state import CPUState
from schemas.coordinator.execution_policy import ExecutionPolicy

class CoordinatorInput(BaseModel):
    state: CPUState
    correlation_id: str
    execution_mode: ExecutionPolicy = Field(default=ExecutionPolicy.SEQUENTIAL)

    class Config:
        json_schema_extra = {
            "title": "CoordinatorInput",
            "description": "Input payload for the MultiAgentCoordinator.",
        }

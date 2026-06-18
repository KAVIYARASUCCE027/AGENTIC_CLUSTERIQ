"""
Memory Agent — Phase 10.
"""
import logging
from agents.base_agent import BaseAgent
from schemas.cpu_state import CPUState
from services.memory_service import MemoryService
from enums.memory_source import MemorySource
from schemas.memory_output import MemoryOutputState

logger = logging.getLogger(__name__)

class MemoryAgent(BaseAgent):
    def __init__(self):
        self._service = MemoryService()

    @property
    def name(self) -> str:
        return "memory"

    def execute(self, state: CPUState) -> CPUState:
        try:
            # 1. Retrieve historical context
            memory_output = self._service.retrieve_context(
                pod_name=state.inputs.pod_name,
                namespace=state.inputs.namespace,
                root_cause=state.root_cause_output.root_cause.value,
                severity=state.analyzer_output.severity.value,
            )
        except Exception as e:
            logger.warning("MemoryAgent retrieval fallback triggered: %s", str(e))
            memory_output = MemoryOutputState(source=MemorySource.FALLBACK)

        try:
            # 2. Save current incident
            incident_id = self._service.save_incident(state)
            logger.info("Saved incident record to DB. ID: %s", incident_id)
        except Exception as e:
            logger.warning("MemoryAgent save fallback triggered: %s", str(e))

        return state.model_copy(update={"memory_output": memory_output})

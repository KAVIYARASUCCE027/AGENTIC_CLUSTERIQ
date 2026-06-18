"""
Analyzer Agent — Phase 10.
"""
from agents.base_agent import BaseAgent
from schemas.cpu_state import CPUState
from services.analyzer_service import AnalyzerService

class AnalyzerAgent(BaseAgent):
    def __init__(self):
        self._service = AnalyzerService()

    @property
    def name(self) -> str:
        return "analyzer"

    def execute(self, state: CPUState) -> CPUState:
        # Pass required inputs to the Analyzer Service
        output = self._service.analyze(
            cpu_usage_percent=state.metrics.cpu_usage,
            cpu_limit=state.metrics.cpu_limit,
            cpu_request=state.metrics.cpu_request,
            restart_count=state.metrics.restart_count,
            replica_count=state.metrics.replica_count,
            cpu_usage_5m_avg=state.metrics.avg_cpu_last_5m,
            cpu_usage_15m_avg=state.metrics.avg_cpu_last_15m,
        )
        return state.model_copy(update={"analyzer_output": output})

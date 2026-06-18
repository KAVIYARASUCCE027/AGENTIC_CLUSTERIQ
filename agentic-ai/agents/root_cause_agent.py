"""
Root Cause Agent — Phase 10.
"""
from agents.base_agent import BaseAgent
from schemas.cpu_state import CPUState
from services.ai.gemini_root_cause_service import GeminiRootCauseService
from services.fallback_root_cause_service import FallbackRootCauseService

class RootCauseAgent(BaseAgent):
    def __init__(self):
        self._gemini = GeminiRootCauseService()
        self._fallback = FallbackRootCauseService()

    @property
    def name(self) -> str:
        return "root_cause"

    def execute(self, state: CPUState) -> CPUState:
        try:
            output = self._gemini.analyze_root_cause(
                metrics=state.metrics,
                analyzer_output=state.analyzer_output
            )
        except Exception as e:
            output = self._fallback.analyze_root_cause(
                metrics=state.metrics,
                analyzer_output=state.analyzer_output
            )
        return state.model_copy(update={"root_cause_output": output})

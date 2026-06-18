"""
Action Planner Agent — Phase 10.
"""
import logging
from agents.base_agent import BaseAgent
from schemas.cpu_state import CPUState
from services.ai.gemini_action_planner_service import GeminiActionPlannerService
from services.fallback_action_planner_service import FallbackActionPlannerService

logger = logging.getLogger(__name__)

class ActionPlannerAgent(BaseAgent):
    def __init__(self):
        self._gemini = GeminiActionPlannerService()
        self._fallback = FallbackActionPlannerService()

    @property
    def name(self) -> str:
        return "action_planner"

    def execute(self, state: CPUState) -> CPUState:
        try:
            output = self._gemini.generate_action_plan(
                metrics=state.metrics,
                analyzer_output=state.analyzer_output,
                root_cause_output=state.root_cause_output,
                recommendation_output=state.recommendation_output
            )
        except Exception as e:
            logger.warning("ActionPlannerAgent fallback triggered: %s", str(e))
            output = self._fallback.generate_action_plan(
                metrics=state.metrics,
                analyzer_output=state.analyzer_output,
                root_cause_output=state.root_cause_output,
                recommendation_output=state.recommendation_output
            )
        return state.model_copy(update={"action_plan_output": output})

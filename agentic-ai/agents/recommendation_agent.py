"""
Recommendation Agent — Phase 10.
"""
import logging
from agents.base_agent import BaseAgent
from schemas.cpu_state import CPUState
from services.ai.gemini_recommendation_service import GeminiRecommendationService
from services.fallback_recommendation_service import FallbackRecommendationService

logger = logging.getLogger(__name__)

class RecommendationAgent(BaseAgent):
    def __init__(self):
        self._gemini = GeminiRecommendationService()
        self._fallback = FallbackRecommendationService()

    @property
    def name(self) -> str:
        return "recommendation"

    def execute(self, state: CPUState) -> CPUState:
        try:
            output = self._gemini.generate_recommendations(
                metrics=state.metrics,
                analyzer_output=state.analyzer_output,
                root_cause_output=state.root_cause_output
            )
        except Exception as e:
            logger.warning("RecommendationAgent fallback triggered: %s", str(e))
            output = self._fallback.generate_recommendations(
                metrics=state.metrics,
                analyzer_output=state.analyzer_output,
                root_cause_output=state.root_cause_output
            )
        return state.model_copy(update={"recommendation_output": output})

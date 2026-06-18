from schemas.cpu_state import CPUState
from services.rules.base_rule import BaseRule, RuleResult
import config.analyzer_constants as constants

class HistoryRule(BaseRule):
    """
    Integrates incident history to detect recurring patterns.
    """

    def evaluate(self, state: CPUState) -> RuleResult:
        result = RuleResult()
        previous_incidents = state.memory.previous_incidents
        
        if previous_incidents:
            result.reasoning.append(
                f"Found {len(previous_incidents)} previous incidents for this pod/namespace."
            )
            result.confidence_score += constants.CONFIDENCE_HISTORY_EXISTS
            
        return result

from schemas.cpu_state import CPUState
from schemas.analyzer_output import Severity
from services.rules.base_rule import BaseRule, RuleResult
import config.analyzer_constants as constants

class RestartRule(BaseRule):
    """
    Analyzes pod restart patterns.
    """

    def evaluate(self, state: CPUState) -> RuleResult:
        result = RuleResult()
        restarts = state.metrics.restart_count
        
        if restarts > constants.RESTART_THRESHOLD:
            result.root_cause = "POD_RESTARTING"
            result.severity = Severity.HIGH
            result.reasoning.append(f"Pod restarted multiple times (count: {restarts}).")
            result.recommendations.append("Check previous pod logs for crash reasons (OOMKilled, panics).")
            result.action_plan.append("Run 'kubectl logs --previous' to investigate.")
            result.confidence_score += constants.CONFIDENCE_RESTARTS_OVER_3
            
        return result

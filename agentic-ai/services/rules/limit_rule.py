from schemas.cpu_state import CPUState
from schemas.analyzer_output import AbnormalityType
from services.rules.base_rule import BaseRule, RuleResult
import config.analyzer_constants as constants

class LimitRule(BaseRule):
    """
    Analyzes if usage approaches or hits the CPU limit.
    """

    def evaluate(self, state: CPUState) -> RuleResult:
        result = RuleResult()
        cpu = state.metrics.cpu_usage
        limit = state.metrics.cpu_limit
        
        # We consider "approaching limit" if usage > 90% and limits exist.
        # However, cpu_usage is often a percentage relative to the limit already if correctly scaled.
        # Assuming cpu_usage is already a percentage of the limit or request.
        if limit > 0 and cpu >= constants.THROTTLING_LIMIT_THRESHOLD:
            result.abnormality = AbnormalityType.THROTTLING_RISK
            result.root_cause = "CPU_LIMIT_REACHED"
            result.reasoning.append(f"CPU usage ({cpu}%) is approaching the configured limit.")
            result.recommendations.append("Increase CPU limits.")
            result.action_plan.append("Patch deployment to increase CPU limits.")
            
        return result

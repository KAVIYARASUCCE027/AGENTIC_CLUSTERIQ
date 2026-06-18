from schemas.cpu_state import CPUState
from schemas.analyzer_output import AbnormalityType
from services.rules.base_rule import BaseRule, RuleResult
import config.analyzer_constants as constants

class SustainedCPURule(BaseRule):
    """
    Detects sustained high CPU usage over time.
    """

    def evaluate(self, state: CPUState) -> RuleResult:
        result = RuleResult()
        cpu = state.metrics.cpu_usage
        avg_5m = state.metrics.avg_cpu_last_5m
        avg_15m = state.metrics.avg_cpu_last_15m
        
        is_sustained = (
            cpu >= constants.SUSTAINED_CURRENT_MIN and
            avg_5m >= constants.SUSTAINED_5M_MIN and
            avg_15m >= constants.SUSTAINED_15M_MIN
        )
        
        if is_sustained:
            result.abnormality = AbnormalityType.SUSTAINED_HIGH_CPU
            result.reasoning.append(
                f"Sustained high CPU: current {cpu}%, 5m avg {avg_5m}%, 15m avg {avg_15m}%."
            )
            result.recommendations.append("Profile application for performance bottlenecks.")
            result.action_plan.append("Analyze CPU flamegraphs or thread dumps.")
            
        if avg_5m >= constants.SUSTAINED_5M_MIN:
            result.confidence_score += constants.CONFIDENCE_5M_OVER_85
            
        if avg_15m >= constants.SUSTAINED_15M_MIN:
            result.confidence_score += constants.CONFIDENCE_15M_OVER_80
            
        return result

from schemas.cpu_state import CPUState
from schemas.analyzer_output import AbnormalityType
from services.rules.base_rule import BaseRule, RuleResult
import config.analyzer_constants as constants

class SpikeRule(BaseRule):
    """
    Detects sudden spikes in CPU usage.
    """

    def evaluate(self, state: CPUState) -> RuleResult:
        result = RuleResult()
        cpu = state.metrics.cpu_usage
        avg_5m = state.metrics.avg_cpu_last_5m
        
        if cpu >= constants.SPIKE_CURRENT_MIN and avg_5m <= constants.SPIKE_AVG_MAX:
            result.abnormality = AbnormalityType.CPU_SPIKE
            result.reasoning.append(
                f"Sudden CPU spike detected: current is {cpu}%, but 5m average is only {avg_5m}%."
            )
            result.recommendations.append("Investigate recent workload bursts or cronjobs.")
            result.action_plan.append("Check application logs for sudden traffic spikes or background jobs.")
            result.confidence_score += 10 # Slight bump for spike detection
            
        return result

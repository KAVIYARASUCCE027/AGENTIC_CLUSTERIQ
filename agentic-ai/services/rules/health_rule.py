from schemas.cpu_state import CPUState
from schemas.analyzer_output import HealthStatus, Severity
from services.rules.base_rule import BaseRule, RuleResult
import config.analyzer_constants as constants

class HealthRule(BaseRule):
    """
    Classifies the overall health status based on current CPU usage.
    """

    def evaluate(self, state: CPUState) -> RuleResult:
        cpu = state.metrics.cpu_usage
        result = RuleResult()
        
        if cpu <= constants.CPU_NORMAL_MAX:
            result.status = HealthStatus.NORMAL
            result.severity = Severity.LOW
            result.reasoning.append(f"CPU usage is normal at {cpu}%.")
        elif cpu <= constants.CPU_HEALTHY_MAX:
            result.status = HealthStatus.HEALTHY
            result.severity = Severity.LOW
            result.reasoning.append(f"CPU usage is healthy at {cpu}%.")
        elif cpu <= constants.CPU_WARNING_MAX:
            result.status = HealthStatus.WARNING
            result.severity = Severity.MEDIUM
            result.reasoning.append(f"CPU usage is elevated at {cpu}%.")
        elif cpu <= constants.CPU_HIGH_MAX:
            result.status = HealthStatus.HIGH
            result.severity = Severity.HIGH
            result.reasoning.append(f"CPU usage is high at {cpu}%.")
        else:
            result.status = HealthStatus.CRITICAL
            result.severity = Severity.CRITICAL
            result.reasoning.append(f"CPU usage is critical at {cpu}%.")
            result.confidence_score += constants.CONFIDENCE_CPU_OVER_90

        return result

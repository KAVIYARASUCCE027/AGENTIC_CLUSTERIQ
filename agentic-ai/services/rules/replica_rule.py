from schemas.cpu_state import CPUState
from services.rules.base_rule import BaseRule, RuleResult
import config.analyzer_constants as constants

class ReplicaRule(BaseRule):
    """
    Analyzes if the pod lacks sufficient replicas for high load.
    """

    def evaluate(self, state: CPUState) -> RuleResult:
        result = RuleResult()
        cpu = state.metrics.cpu_usage
        replicas = state.metrics.replica_count
        
        if cpu > constants.CPU_REPLICA_THRESHOLD and replicas == constants.REPLICA_MIN_COUNT:
            result.root_cause = "INSUFFICIENT_REPLICAS"
            result.reasoning.append("High CPU load with only 1 replica running.")
            result.recommendations.append("Increase replicas.")
            result.action_plan.append("Enable Horizontal Pod Autoscaler (HPA).")
            
        return result

from schemas.cpu_state import CPUState
from schemas.analyzer_output import AbnormalityType
from services.rules.base_rule import BaseRule, RuleResult
import config.analyzer_constants as constants

class NodeContentionRule(BaseRule):
    """
    Detects possible noisy neighbor or node resource contention.
    """

    def evaluate(self, state: CPUState) -> RuleResult:
        result = RuleResult()
        cpu = state.metrics.cpu_usage
        restarts = state.metrics.restart_count
        
        # Simplified assumption for node CPU. A real system would have the node CPU.
        # But we will write the logic per requirements. The instructions say:
        # "If Pod CPU high, Restart count low, CPU limit normal, Node CPU > 95%"
        # Since we don't have Node CPU yet, we simulate or skip unless added.
        # We'll just leave it ready for expansion.
        
        node_cpu = 0.0 # Placeholder
        
        if (cpu > constants.NODE_CONTENTION_POD_LIMIT_PERCENTAGE and 
            restarts <= constants.RESTART_THRESHOLD and 
            node_cpu > constants.NODE_CPU_CONTENTION_THRESHOLD):
            
            result.abnormality = AbnormalityType.NODE_RESOURCE_CONTENTION
            result.root_cause = "NODE_RESOURCE_CONTENTION"
            result.reasoning.append("Possible noisy neighbor: pod CPU is high, node CPU is highly contended.")
            result.recommendations.append("Migrate pod to a less contended node or check other workloads.")
            result.action_plan.append("Cordon the node and evict the pod.")
            
        return result

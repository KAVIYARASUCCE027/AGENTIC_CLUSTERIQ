from schemas.cpu_state import CPUState
from schemas.analyzer_output import AnalyzerOutputState, HealthStatus, Severity, AbnormalityType
from services.rules.health_rule import HealthRule
from services.rules.spike_rule import SpikeRule
from services.rules.sustained_cpu_rule import SustainedCPURule
from services.rules.limit_rule import LimitRule
from services.rules.restart_rule import RestartRule
from services.rules.replica_rule import ReplicaRule
from services.rules.node_contention_rule import NodeContentionRule
from services.rules.trend_rule import TrendRule
from services.rules.history_rule import HistoryRule
import config.analyzer_constants as constants
from utils.logger import get_logger

logger = get_logger(__name__)

class AnalyzerService:
    """
    Production-grade rule-based engine to deterministically analyze CPU state.
    """
    
    def __init__(self):
        # Registry pattern for easy extensibility
        self.rules = [
            HealthRule(),
            SpikeRule(),
            SustainedCPURule(),
            LimitRule(),
            RestartRule(),
            ReplicaRule(),
            NodeContentionRule(),
            TrendRule(),
            HistoryRule()
        ]

    def analyze(self, state: CPUState) -> AnalyzerOutputState:
        """
        Executes all registered rules against the CPUState.
        Aggregates the results into a single AnalyzerOutputState.
        """
        logger.info(f"AnalyzerService: Beginning analysis for {state.inputs.namespace}/{state.inputs.pod_name}")
        
        output = AnalyzerOutputState()
        
        for rule in self.rules:
            result = rule.evaluate(state)
            
            # Aggregate status (prioritize higher severity statuses)
            # A simple approach: if rule returned a status, we assume HealthRule did it.
            # Real aggregation might compare enum weights.
            if result.status and result.status != HealthStatus.NORMAL:
                output.health_status = result.status
            elif result.status == HealthStatus.NORMAL and output.health_status == HealthStatus.NORMAL:
                output.health_status = HealthStatus.NORMAL
                
            # Aggregate severity
            if result.severity and result.severity != Severity.LOW:
                # Assuming simple string comparison for severity levels or overriding
                # Since HealthRule sets it first, others can bump it up.
                output.severity = result.severity
                
            # Aggregate abnormality
            if result.abnormality and result.abnormality != AbnormalityType.NONE:
                output.abnormality = result.abnormality
                
            # Aggregate root cause (first one wins or concatenate)
            if result.root_cause:
                if not output.root_cause:
                    output.root_cause = result.root_cause
                else:
                    output.root_cause += f" | {result.root_cause}"
                    
            # Aggregate trend
            if result.trend:
                output.trend = result.trend
                
            # Aggregate reasoning and recommendations
            output.reasoning.extend(result.reasoning)
            output.recommendations.extend(result.recommendations)
            output.action_plan.extend(result.action_plan)
            
            # Aggregate confidence score
            output.confidence += result.confidence_score

        # Cap confidence at max (100)
        output.confidence = min(output.confidence, constants.CONFIDENCE_MAX)
        
        logger.info(f"AnalyzerService: Analysis complete. Status: {output.health_status.value}, Confidence: {output.confidence}")
        
        return output

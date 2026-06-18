from schemas.cpu_state import CPUState, CPUTrend
from services.rules.base_rule import BaseRule, RuleResult

class TrendRule(BaseRule):
    """
    Analyzes the trend of CPU usage.
    """

    def evaluate(self, state: CPUState) -> RuleResult:
        result = RuleResult()
        trend = state.metrics.cpu_trend
        
        if trend == CPUTrend.INCREASING:
            result.trend = "INCREASING"
            result.reasoning.append("CPU behavior is worsening (trend is increasing).")
        elif trend == CPUTrend.DECREASING:
            result.trend = "RECOVERING"
            result.reasoning.append("CPU behavior is improving (trend is decreasing).")
        else:
            result.trend = "STABLE"
            
        return result

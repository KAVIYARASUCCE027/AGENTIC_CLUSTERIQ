import pytest
from schemas.cpu_state import CPUState, MetricState, InputState, CPUTrend
from services.rules.trend_rule import TrendRule

def test_trend_rule():
    state = CPUState(
        inputs=InputState(pod_name="test", namespace="test"), 
        metrics=MetricState(cpu_trend=CPUTrend.INCREASING)
    )
    rule = TrendRule()
    result = rule.evaluate(state)
    assert result.trend == "INCREASING"

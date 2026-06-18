import pytest
from schemas.cpu_state import CPUState, MetricState, InputState
from schemas.analyzer_output import AbnormalityType
from services.rules.limit_rule import LimitRule

def test_limit_rule():
    state = CPUState(
        inputs=InputState(pod_name="test", namespace="test"), 
        metrics=MetricState(cpu_usage=95.0, cpu_limit=100.0)
    )
    rule = LimitRule()
    result = rule.evaluate(state)
    assert result.abnormality == AbnormalityType.THROTTLING_RISK
    assert result.root_cause == "CPU_LIMIT_REACHED"

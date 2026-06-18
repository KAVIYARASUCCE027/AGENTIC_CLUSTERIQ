import pytest
from schemas.cpu_state import CPUState, MetricState, InputState
from schemas.analyzer_output import Severity
from services.rules.restart_rule import RestartRule

def test_restart_rule():
    state = CPUState(
        inputs=InputState(pod_name="test", namespace="test"), 
        metrics=MetricState(restart_count=4)
    )
    rule = RestartRule()
    result = rule.evaluate(state)
    assert result.root_cause == "POD_RESTARTING"
    assert result.severity == Severity.HIGH

import pytest
from schemas.cpu_state import CPUState, MetricState, InputState
from schemas.analyzer_output import HealthStatus, Severity
from services.rules.health_rule import HealthRule

def test_health_rule_normal():
    state = CPUState(inputs=InputState(pod_name="test", namespace="test"), metrics=MetricState(cpu_usage=40.0))
    rule = HealthRule()
    result = rule.evaluate(state)
    assert result.status == HealthStatus.NORMAL
    assert result.severity == Severity.LOW

def test_health_rule_critical():
    state = CPUState(inputs=InputState(pod_name="test", namespace="test"), metrics=MetricState(cpu_usage=95.0))
    rule = HealthRule()
    result = rule.evaluate(state)
    assert result.status == HealthStatus.CRITICAL
    assert result.severity == Severity.CRITICAL

import pytest
from schemas.cpu_state import CPUState, MetricState, InputState
from services.analyzer_service import AnalyzerService
from schemas.analyzer_output import HealthStatus, AbnormalityType

def test_analyzer_service_aggregation():
    # Simulate a pod experiencing a sudden spike
    state = CPUState(
        inputs=InputState(pod_name="test", namespace="test"),
        metrics=MetricState(
            cpu_usage=95.0,
            avg_cpu_last_5m=40.0,
            avg_cpu_last_15m=35.0,
            restart_count=4,
            replica_count=1,
            cpu_limit=0.0
        )
    )
    
    service = AnalyzerService()
    output = service.analyze(state)
    
    assert output.health_status == HealthStatus.CRITICAL
    assert output.abnormality == AbnormalityType.CPU_SPIKE
    assert "POD_RESTARTING" in output.root_cause
    assert "INSUFFICIENT_REPLICAS" in output.root_cause
    assert output.confidence > 50
    assert len(output.reasoning) > 0

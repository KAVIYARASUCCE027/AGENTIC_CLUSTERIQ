"""
Tests for Incident Repository.
"""
import pytest
from datetime import datetime, timezone

from config.settings import get_settings
from schemas.memory.incident_record import (
    IncidentRecord, MetricsSnapshot, AnalyzerSnapshot, 
    RootCauseSnapshot, RecommendationSnapshot, ActionPlanSnapshot
)
from repositories.incident_repository import IncidentRepository


import os

@pytest.fixture(autouse=True)
def setup_test_db():
    os.environ["TESTING"] = "true"
    yield
    os.environ.pop("TESTING", None)
    # The client singleton handles the mongomock initialization internally


@pytest.fixture
def repo():
    return IncidentRepository()


def _make_record() -> IncidentRecord:
    return IncidentRecord(
        execution_id="exec-123",
        pod_name="api-pod",
        namespace="prod",
        metrics=MetricsSnapshot(
            cpu_usage=90.0, avg_cpu_5m=85.0, avg_cpu_15m=80.0,
            cpu_trend="INCREASING", cpu_limit=1000.0, cpu_request=500.0,
            restart_count=0, replica_count=1,
        ),
        analyzer=AnalyzerSnapshot(
            health_status="CRITICAL", severity="HIGH",
            abnormality="SUSTAINED_HIGH_CPU", confidence=90,
        ),
        root_cause=RootCauseSnapshot(
            root_cause="CPU_LIMIT_REACHED", confidence=85, evidence=[],
        ),
        recommendation=RecommendationSnapshot(
            recommendations=["INCREASE_CPU_LIMIT"], confidence=85,
        ),
        action_plan=ActionPlanSnapshot(
            action_types=["PATCH_DEPLOYMENT"], priority="HIGH", risk="MEDIUM", confidence=85,
        )
    )


class TestIncidentRepository:

    def test_save_and_find_by_id(self, repo):
        rec = _make_record()
        repo.save(rec)
        
        found = repo.find_by_id(rec.incident_id)
        assert found is not None
        assert found.incident_id == rec.incident_id
        assert found.pod_name == "api-pod"

    def test_list_recent(self, repo):
        # Insert 3 records
        for _ in range(3):
            repo.save(_make_record())
            
        recent = repo.list_recent(limit=2)
        assert len(recent) == 2

    def test_archive(self, repo):
        rec = _make_record()
        repo.save(rec)
        
        success = repo.archive(rec.incident_id)
        assert success is True
        
        found = repo.find_by_id(rec.incident_id)
        assert found.status.value == "ARCHIVED"

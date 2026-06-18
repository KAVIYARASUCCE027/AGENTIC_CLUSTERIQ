"""
Tests for MemoryService.
Verifies DB integration, context building, and similarity matching (mocked pipeline).
"""
import pytest
from unittest.mock import patch, MagicMock

from config.settings import get_settings
from services.memory_service import MemoryService
from enums.memory_source import MemorySource


import os

@pytest.fixture(autouse=True)
def setup_test_db():
    os.environ["TESTING"] = "true"
    yield
    os.environ.pop("TESTING", None)


@pytest.fixture
def service():
    return MemoryService()


class TestMemoryService:

    @patch("services.memory_service.MemoryRepository")
    def test_retrieve_context_with_matches(self, mock_repo_cls):
        mock_repo = mock_repo_cls.return_value
        # Mock what the DB aggregate pipeline would return
        mock_repo.find_similar.return_value = [
            {
                "incident_id": "test-id-1",
                "pod_name": "api-pod",
                "timestamp": "2026-06-18T10:00:00Z",
                "root_cause": {"root_cause": "CPU_LIMIT_REACHED"},
                "analyzer": {"severity": "HIGH"},
                "status": "RESOLVED",
                "similarity_score": 0.8
            }
        ]
        mock_repo.extract_patterns.return_value = [
            {"_id": "CPU_LIMIT_REACHED", "count": 3}
        ]
        
        service = MemoryService()
        output = service.retrieve_context("api-pod", "prod", "CPU_LIMIT_REACHED", "HIGH")
        
        assert output.source == MemorySource.MONGODB
        assert output.incident_count == 1
        assert len(output.similar_incidents) == 1
        assert len(output.historical_patterns) == 1
        assert "1 similar incidents found" in output.memory_summary.context

    @patch("services.memory_service.MemoryRepository")
    def test_retrieve_context_empty(self, mock_repo_cls):
        mock_repo = mock_repo_cls.return_value
        mock_repo.find_similar.return_value = []
        mock_repo.extract_patterns.return_value = []
        
        service = MemoryService()
        output = service.retrieve_context("new-pod", "prod", "UNKNOWN", "LOW")
        
        assert output.incident_count == 0
        assert "No history available" in output.memory_summary.context

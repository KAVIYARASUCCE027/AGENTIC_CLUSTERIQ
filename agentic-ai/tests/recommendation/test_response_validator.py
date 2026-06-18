"""
Tests for RecommendationResponseValidator.
Covers: invalid JSON, missing fields, invalid enum values, confidence clamp,
empty recommendations, markdown fences, and trailing commas.
"""
import pytest
from services.recommendation_response_validator import RecommendationResponseValidator


@pytest.fixture
def validator():
    return RecommendationResponseValidator()


def _valid_payload() -> str:
    return """{
        "recommendations": ["INCREASE_CPU_LIMIT", "ENABLE_HPA"],
        "reasoning": ["CPU at limit", "HPA prevents future spikes"],
        "confidence": 88,
        "possible_recommendations": [
            {"recommendation": "SCALE_UP_REPLICAS", "confidence": 70, "priority": "MEDIUM", "description": "Add replicas"}
        ]
    }"""


class TestRecommendationResponseValidator:

    def test_valid_response(self, validator):
        result = validator.validate(_valid_payload())
        assert "INCREASE_CPU_LIMIT" in result["recommendations"]
        assert result["confidence"] == 88

    def test_empty_response_returns_fallback(self, validator):
        result = validator.validate("")
        assert result["recommendations"] == ["MONITOR_CLOSELY"]
        assert result["confidence"] == 0

    def test_invalid_json_returns_fallback(self, validator):
        result = validator.validate("{ not json {{")
        assert "MONITOR_CLOSELY" in result["recommendations"]

    def test_strips_markdown_fences(self, validator):
        raw = "```json\n" + _valid_payload() + "\n```"
        result = validator.validate(raw)
        assert "INCREASE_CPU_LIMIT" in result["recommendations"]

    def test_repairs_trailing_comma(self, validator):
        raw = '{"recommendations":["ENABLE_HPA",],"reasoning":["test"],"confidence":80,"possible_recommendations":[]}'
        result = validator.validate(raw)
        assert "ENABLE_HPA" in result["recommendations"]

    def test_invalid_recommendation_filtered_out(self, validator):
        raw = '{"recommendations":["INVALID_ACTION","ENABLE_HPA"],"reasoning":["x"],"confidence":80,"possible_recommendations":[]}'
        result = validator.validate(raw)
        assert "INVALID_ACTION" not in result["recommendations"]
        assert "ENABLE_HPA" in result["recommendations"]

    def test_all_invalid_recs_fall_back_to_monitor(self, validator):
        raw = '{"recommendations":["MADE_UP_ACTION"],"reasoning":["x"],"confidence":80,"possible_recommendations":[]}'
        result = validator.validate(raw)
        assert result["recommendations"] == ["MONITOR_CLOSELY"]

    def test_confidence_clamped_to_100(self, validator):
        raw = '{"recommendations":["ENABLE_HPA"],"reasoning":["x"],"confidence":999,"possible_recommendations":[]}'
        result = validator.validate(raw)
        assert result["confidence"] == 100

    def test_missing_field_returns_fallback(self, validator):
        raw = '{"recommendations":["ENABLE_HPA"],"confidence":80}'
        result = validator.validate(raw)
        assert "MONITOR_CLOSELY" in result["recommendations"]

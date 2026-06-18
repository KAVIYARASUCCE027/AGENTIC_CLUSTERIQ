"""
Tests for RootCauseResponseValidator.
Covers: malformed JSON, missing fields, invalid enum, confidence clamp,
empty evidence, markdown fences, and trailing commas.
"""
import pytest
from services.root_cause_response_validator import RootCauseResponseValidator


@pytest.fixture
def validator():
    return RootCauseResponseValidator()


def _valid_payload() -> str:
    return """{
        "root_cause": "CPU_LIMIT_REACHED",
        "confidence": 88,
        "evidence": ["CPU usage at 95%"],
        "reasoning": ["Approaching configured limit"],
        "possible_causes": [{"cause": "INSUFFICIENT_REPLICAS", "confidence": 60}]
    }"""


class TestRootCauseResponseValidator:

    def test_valid_response(self, validator):
        result = validator.validate(_valid_payload())
        assert result["root_cause"] == "CPU_LIMIT_REACHED"
        assert result["confidence"] == 88

    def test_empty_response_returns_fallback(self, validator):
        result = validator.validate("")
        assert result["root_cause"] == "UNKNOWN"
        assert result["confidence"] == 0

    def test_invalid_json_returns_fallback(self, validator):
        result = validator.validate("this is not json {{{")
        assert result["root_cause"] == "UNKNOWN"

    def test_strips_markdown_fences(self, validator):
        raw = "```json\n" + _valid_payload() + "\n```"
        result = validator.validate(raw)
        assert result["root_cause"] == "CPU_LIMIT_REACHED"

    def test_repairs_trailing_comma(self, validator):
        raw = '{"root_cause":"CPU_LIMIT_REACHED","confidence":80,"evidence":["x",],"reasoning":["y"],"possible_causes":[]}'
        result = validator.validate(raw)
        assert result["root_cause"] == "CPU_LIMIT_REACHED"

    def test_invalid_root_cause_forced_to_unknown(self, validator):
        raw = '{"root_cause":"MADE_UP_CAUSE","confidence":90,"evidence":["x"],"reasoning":["y"],"possible_causes":[]}'
        result = validator.validate(raw)
        assert result["root_cause"] == "UNKNOWN"
        assert result["confidence"] == 0

    def test_confidence_clamped_to_100(self, validator):
        raw = '{"root_cause":"CPU_LIMIT_REACHED","confidence":999,"evidence":["x"],"reasoning":["y"],"possible_causes":[]}'
        result = validator.validate(raw)
        assert result["confidence"] == 100

    def test_empty_evidence_gets_placeholder(self, validator):
        raw = '{"root_cause":"CPU_LIMIT_REACHED","confidence":80,"evidence":[],"reasoning":["y"],"possible_causes":[]}'
        result = validator.validate(raw)
        assert len(result["evidence"]) >= 1

    def test_missing_field_returns_fallback(self, validator):
        raw = '{"root_cause":"CPU_LIMIT_REACHED","confidence":80}'
        result = validator.validate(raw)
        assert result["root_cause"] == "UNKNOWN"

"""
Tests for ActionPlanResponseValidator.
"""
import pytest
from services.action_plan_response_validator import ActionPlanResponseValidator


@pytest.fixture
def validator():
    return ActionPlanResponseValidator()


def _valid_payload() -> str:
    return """{
        "actions": [
            {
                "step": 1,
                "action": "Increase CPU limits",
                "action_type": "PATCH_DEPLOYMENT",
                "risk": "LOW",
                "estimated_duration": "2 minutes"
            }
        ],
        "priority": "HIGH",
        "risk": "LOW",
        "estimated_duration": "2 minutes",
        "rollback_strategy": "Revert",
        "confidence": 90
    }"""


class TestActionPlanResponseValidator:

    def test_valid_response(self, validator):
        result = validator.validate(_valid_payload())
        assert len(result["actions"]) == 1
        assert result["actions"][0]["action_type"] == "PATCH_DEPLOYMENT"
        assert result["confidence"] == 90

    def test_empty_response_returns_fallback(self, validator):
        result = validator.validate("")
        assert result["actions"][0]["action_type"] == "NO_ACTION"
        assert result["confidence"] == 0

    def test_invalid_json_returns_fallback(self, validator):
        result = validator.validate("{ not json {{")
        assert result["actions"][0]["action_type"] == "NO_ACTION"

    def test_strips_markdown_fences(self, validator):
        raw = "```json\n" + _valid_payload() + "\n```"
        result = validator.validate(raw)
        assert result["actions"][0]["action_type"] == "PATCH_DEPLOYMENT"

    def test_repairs_trailing_comma(self, validator):
        raw = '{"actions":[{"step":1,"action":"do it","action_type":"KUBECTL_COMMAND"}],"priority":"LOW","risk":"LOW","estimated_duration":"1m","rollback_strategy":"none","confidence":80,}'
        result = validator.validate(raw)
        assert len(result["actions"]) == 1

    def test_invalid_action_type_forces_no_action(self, validator):
        raw = '{"actions":[{"step":1,"action":"do it","action_type":"MADE_UP_COMMAND"}],"priority":"LOW","risk":"LOW","estimated_duration":"1m","rollback_strategy":"none","confidence":80}'
        result = validator.validate(raw)
        assert result["actions"][0]["action_type"] == "NO_ACTION"

    def test_invalid_priority_forces_low(self, validator):
        raw = '{"actions":[{"step":1,"action":"do it","action_type":"KUBECTL_COMMAND"}],"priority":"URGENT","risk":"LOW","estimated_duration":"1m","rollback_strategy":"none","confidence":80}'
        result = validator.validate(raw)
        assert result["priority"] == "LOW"

    def test_confidence_clamped_to_100(self, validator):
        raw = '{"actions":[{"step":1,"action":"do it","action_type":"KUBECTL_COMMAND"}],"priority":"LOW","risk":"LOW","estimated_duration":"1m","rollback_strategy":"none","confidence":999}'
        result = validator.validate(raw)
        assert result["confidence"] == 100

    def test_missing_field_returns_fallback(self, validator):
        raw = '{"actions":[{"step":1,"action":"do it","action_type":"KUBECTL_COMMAND"}],"confidence":80}'
        result = validator.validate(raw)
        assert result["actions"][0]["action_type"] == "NO_ACTION"

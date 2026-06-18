"""
Action Planner Response Validator — Phase 8.

Validates and repairs raw JSON responses from Gemini before they are
parsed into ActionPlanOutputState.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

from enums.action_type import ActionType
from enums.action_priority import ActionPriority
from enums.action_risk import ActionRisk

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = {"actions", "priority", "risk", "estimated_duration", "rollback_strategy", "confidence"}
_VALID_ACTION_TYPES = {at.value for at in ActionType}
_VALID_PRIORITIES = {ap.value for ap in ActionPriority}
_VALID_RISKS = {ar.value for ar in ActionRisk}

_FALLBACK_RESPONSE: Dict[str, Any] = {
    "actions": [
        {
            "step": 1,
            "action": "Monitor system closely; plan generation failed.",
            "action_type": "NO_ACTION",
            "risk": "LOW",
            "estimated_duration": "Ongoing"
        }
    ],
    "priority": "LOW",
    "risk": "LOW",
    "estimated_duration": "Unknown",
    "rollback_strategy": "N/A",
    "confidence": 0,
}


def _strip_markdown_fences(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _repair_trailing_commas(raw: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", raw)


class ActionPlanResponseValidator:
    """Validates and sanitises raw Gemini text into a clean dict."""

    def validate(self, raw_response: str) -> Dict[str, Any]:
        if not raw_response or not raw_response.strip():
            logger.error("ActionPlanResponseValidator: Empty response from Gemini.")
            return _FALLBACK_RESPONSE.copy()

        cleaned = _strip_markdown_fences(raw_response)
        cleaned = _repair_trailing_commas(cleaned)

        try:
            data: Dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("ActionPlanResponseValidator: JSON decode failed: %s", e)
            return _FALLBACK_RESPONSE.copy()

        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            logger.warning("ActionPlanResponseValidator: Missing fields %s.", missing)
            return _FALLBACK_RESPONSE.copy()

        # Validate top-level enums
        if data.get("priority") not in _VALID_PRIORITIES:
            data["priority"] = "LOW"
        if data.get("risk") not in _VALID_RISKS:
            data["risk"] = "LOW"

        # Clamp confidence
        try:
            data["confidence"] = max(0, min(100, int(data["confidence"])))
        except (TypeError, ValueError):
            data["confidence"] = 0

        # Validate actions list
        raw_actions = data.get("actions", [])
        if not isinstance(raw_actions, list) or not raw_actions:
            logger.warning("ActionPlanResponseValidator: Invalid or empty actions list.")
            return _FALLBACK_RESPONSE.copy()

        valid_actions = []
        for i, act in enumerate(raw_actions, start=1):
            if not isinstance(act, dict):
                continue
            
            # Extract and validate fields
            action_desc = str(act.get("action", ""))
            if not action_desc:
                continue
                
            action_type = act.get("action_type")
            if action_type not in _VALID_ACTION_TYPES:
                action_type = "NO_ACTION"
                
            risk = act.get("risk")
            if risk not in _VALID_RISKS:
                risk = "LOW"

            valid_actions.append({
                "step": i,
                "action": action_desc,
                "action_type": action_type,
                "risk": risk,
                "estimated_duration": str(act.get("estimated_duration", "Unknown")),
            })

        if not valid_actions:
            logger.warning("ActionPlanResponseValidator: No valid action steps parsed.")
            return _FALLBACK_RESPONSE.copy()

        data["actions"] = valid_actions

        logger.debug(
            "ActionPlanResponseValidator: Validation passed. actions=%d, confidence=%d",
            len(valid_actions), data["confidence"]
        )
        return data

"""
Root Cause Response Validator — Phase 6.

Validates and repairs raw JSON responses from Gemini before
they are parsed into RootCauseOutputState.

Responsibilities:
    - Strip markdown code fences (Gemini sometimes wraps JSON in ```json ... ```)
    - Validate required fields are present
    - Validate root_cause is a known enum value
    - Validate confidence is within [0, 100]
    - Ensure evidence list is non-empty
    - Return a safe fallback dict on unrecoverable failures
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional

from enums.root_cause_type import RootCauseType

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = {"root_cause", "confidence", "evidence", "reasoning", "possible_causes"}
_VALID_ROOT_CAUSES = {rc.value for rc in RootCauseType}

_FALLBACK_RESPONSE: Dict[str, Any] = {
    "root_cause": "UNKNOWN",
    "confidence": 0,
    "evidence": ["Root cause analysis unavailable due to response parsing failure."],
    "reasoning": ["Gemini response could not be parsed."],
    "possible_causes": [],
}


def _strip_markdown_fences(raw: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers that Gemini sometimes adds."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _repair_trailing_commas(raw: str) -> str:
    """Remove trailing commas before } or ] to fix common JSON malformation."""
    return re.sub(r",\s*([}\]])", r"\1", raw)


class RootCauseResponseValidator:
    """
    Validates and sanitises raw Gemini text into a clean dict
    ready to be parsed by RootCauseOutputState.
    """

    def validate(self, raw_response: str) -> Dict[str, Any]:
        """
        Parse and validate a raw Gemini response string.

        Args:
            raw_response: The raw text output from Gemini.

        Returns:
            A valid dict matching RootCauseOutputState fields,
            or the _FALLBACK_RESPONSE if recovery is not possible.
        """
        if not raw_response or not raw_response.strip():
            logger.error("RootCauseResponseValidator: Empty response from Gemini.")
            return _FALLBACK_RESPONSE.copy()

        # Step 1 — strip markdown fences
        cleaned = _strip_markdown_fences(raw_response)

        # Step 2 — repair trailing commas
        cleaned = _repair_trailing_commas(cleaned)

        # Step 3 — parse JSON
        try:
            data: Dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("RootCauseResponseValidator: JSON decode failed: %s | raw: %.200s", e, raw_response)
            return _FALLBACK_RESPONSE.copy()

        # Step 4 — check required fields
        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            logger.warning("RootCauseResponseValidator: Missing fields %s. Using fallback.", missing)
            return _FALLBACK_RESPONSE.copy()

        # Step 5 — validate root_cause
        if data["root_cause"] not in _VALID_ROOT_CAUSES:
            logger.warning(
                "RootCauseResponseValidator: Invalid root_cause '%s'. Forcing UNKNOWN.",
                data["root_cause"]
            )
            data["root_cause"] = "UNKNOWN"
            data["confidence"] = 0

        # Step 6 — validate confidence
        try:
            conf = int(data["confidence"])
            data["confidence"] = max(0, min(100, conf))
        except (TypeError, ValueError):
            logger.warning("RootCauseResponseValidator: Invalid confidence value. Setting to 0.")
            data["confidence"] = 0

        # Step 7 — ensure evidence is a non-empty list
        if not isinstance(data.get("evidence"), list) or len(data["evidence"]) == 0:
            logger.warning("RootCauseResponseValidator: Missing evidence. Adding placeholder.")
            data["evidence"] = ["No specific metric evidence cited by model."]

        # Step 8 — ensure reasoning is a list
        if not isinstance(data.get("reasoning"), list):
            data["reasoning"] = [str(data.get("reasoning", ""))]

        # Step 9 — ensure possible_causes is a list
        if not isinstance(data.get("possible_causes"), list):
            data["possible_causes"] = []

        logger.debug("RootCauseResponseValidator: Validation passed. root_cause=%s, confidence=%d",
                     data["root_cause"], data["confidence"])
        return data

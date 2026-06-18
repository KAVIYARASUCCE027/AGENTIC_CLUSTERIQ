"""
Recommendation Response Validator — Phase 7.

Validates and repairs raw JSON responses from Gemini before they are
parsed into RecommendationOutputState.

Responsibilities:
    - Strip markdown code fences
    - Validate required fields
    - Validate recommendation values against enum
    - Clamp confidence to [0, 100]
    - Ensure at least one recommendation exists
    - Return safe fallback dict on unrecoverable failure
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

from enums.recommendation_type import RecommendationType

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS       = {"recommendations", "reasoning", "confidence", "possible_recommendations"}
_VALID_RECOMMENDATIONS = {rt.value for rt in RecommendationType}

_FALLBACK_RESPONSE: Dict[str, Any] = {
    "recommendations": ["MONITOR_CLOSELY"],
    "reasoning": ["Recommendation analysis unavailable due to response parsing failure."],
    "confidence": 0,
    "possible_recommendations": [],
}


def _strip_markdown_fences(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _repair_trailing_commas(raw: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", raw)


class RecommendationResponseValidator:
    """Validates and sanitises raw Gemini text into a clean dict."""

    def validate(self, raw_response: str) -> Dict[str, Any]:
        if not raw_response or not raw_response.strip():
            logger.error("RecommendationResponseValidator: Empty response from Gemini.")
            return _FALLBACK_RESPONSE.copy()

        cleaned = _strip_markdown_fences(raw_response)
        cleaned = _repair_trailing_commas(cleaned)

        try:
            data: Dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("RecommendationResponseValidator: JSON decode failed: %s", e)
            return _FALLBACK_RESPONSE.copy()

        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            logger.warning("RecommendationResponseValidator: Missing fields %s.", missing)
            return _FALLBACK_RESPONSE.copy()

        # Validate and filter recommendations
        raw_recs = data.get("recommendations", [])
        if not isinstance(raw_recs, list):
            raw_recs = []
        valid_recs = [r for r in raw_recs if r in _VALID_RECOMMENDATIONS]
        if not valid_recs:
            logger.warning("RecommendationResponseValidator: No valid recommendations. Using MONITOR_CLOSELY.")
            valid_recs = ["MONITOR_CLOSELY"]
        data["recommendations"] = valid_recs

        # Clamp confidence
        try:
            data["confidence"] = max(0, min(100, int(data["confidence"])))
        except (TypeError, ValueError):
            data["confidence"] = 0

        # Ensure reasoning is a list
        if not isinstance(data.get("reasoning"), list):
            data["reasoning"] = [str(data.get("reasoning", ""))]

        # Validate possible_recommendations
        if not isinstance(data.get("possible_recommendations"), list):
            data["possible_recommendations"] = []

        valid_candidates = []
        for c in data["possible_recommendations"]:
            if isinstance(c, dict) and c.get("recommendation") in _VALID_RECOMMENDATIONS:
                valid_candidates.append(c)
        data["possible_recommendations"] = valid_candidates

        logger.debug(
            "RecommendationResponseValidator: Validation passed. recs=%s, confidence=%d",
            valid_recs, data["confidence"]
        )
        return data

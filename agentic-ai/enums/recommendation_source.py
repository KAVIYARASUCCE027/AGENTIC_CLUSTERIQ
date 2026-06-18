"""
RecommendationSource Enum — Phase 7.

Tracks whether the recommendations were produced by Gemini or the
deterministic fallback service for full observability.
"""
from enum import Enum


class RecommendationSource(str, Enum):
    GEMINI   = "GEMINI"
    FALLBACK = "FALLBACK"

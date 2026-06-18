"""
RootCauseSource Enum — Phase 6.

Tracks whether the root cause was determined by Gemini or the deterministic
fallback service. Critical for observability and debugging.
"""
from enum import Enum


class RootCauseSource(str, Enum):
    """
    Indicates which service produced the final root cause result.
    """
    GEMINI   = "GEMINI"
    FALLBACK = "FALLBACK"

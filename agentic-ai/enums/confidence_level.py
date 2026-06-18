"""
ConfidenceLevel Enum — Phase 7.

Maps a numeric confidence score (0–100) to a human-readable band,
used across recommendation and root cause outputs.
"""
from enum import Enum


class ConfidenceLevel(str, Enum):
    VERY_HIGH = "VERY_HIGH"   # 95–100
    HIGH      = "HIGH"        # 80–94
    MEDIUM    = "MEDIUM"      # 60–79
    LOW       = "LOW"         # 0–59

    @classmethod
    def from_score(cls, score: int) -> "ConfidenceLevel":
        """Derive a ConfidenceLevel from a numeric score 0–100."""
        if score >= 95:
            return cls.VERY_HIGH
        elif score >= 80:
            return cls.HIGH
        elif score >= 60:
            return cls.MEDIUM
        return cls.LOW

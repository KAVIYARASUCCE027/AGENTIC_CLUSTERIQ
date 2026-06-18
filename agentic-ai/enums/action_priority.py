"""
ActionPriority Enum — Phase 8.

Defines the priority level for an overall action plan.
"""
from enum import Enum


class ActionPriority(str, Enum):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"

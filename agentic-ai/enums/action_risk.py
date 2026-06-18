"""
ActionRisk Enum — Phase 8.

Defines the risk level associated with executing a particular action.
"""
from enum import Enum


class ActionRisk(str, Enum):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"

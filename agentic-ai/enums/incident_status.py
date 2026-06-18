"""
IncidentStatus Enum — Phase 9.

Tracks the lifecycle of an incident in the memory store.
"""
from enum import Enum


class IncidentStatus(str, Enum):
    OPEN     = "OPEN"
    RESOLVED = "RESOLVED"
    ARCHIVED = "ARCHIVED"

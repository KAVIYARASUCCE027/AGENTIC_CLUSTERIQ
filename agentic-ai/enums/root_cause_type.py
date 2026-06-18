"""
RootCauseType Enum — Phase 6.

Defines all possible root causes that the Root Cause Agent can identify.
Using an enum prevents string literals from leaking into production code.
"""
from enum import Enum


class RootCauseType(str, Enum):
    """
    Canonical root cause classifications for a CPU incident.
    """
    CPU_LIMIT_REACHED         = "CPU_LIMIT_REACHED"
    INSUFFICIENT_REPLICAS     = "INSUFFICIENT_REPLICAS"
    POD_RESTARTING            = "POD_RESTARTING"
    NODE_RESOURCE_CONTENTION  = "NODE_RESOURCE_CONTENTION"
    WORKLOAD_SPIKE            = "WORKLOAD_SPIKE"
    RESOURCE_REQUEST_TOO_LOW  = "RESOURCE_REQUEST_TOO_LOW"
    APPLICATION_BUG           = "APPLICATION_BUG"
    UNKNOWN                   = "UNKNOWN"

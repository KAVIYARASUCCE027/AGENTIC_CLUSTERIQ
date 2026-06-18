"""
RecommendationType Enum — Phase 7.

Canonical set of actionable recommendations the agent can produce.
Using an enum prevents magic strings throughout the codebase.
"""
from enum import Enum


class RecommendationType(str, Enum):
    SCALE_UP_REPLICAS         = "SCALE_UP_REPLICAS"
    ENABLE_HPA                = "ENABLE_HPA"
    INCREASE_CPU_LIMIT        = "INCREASE_CPU_LIMIT"
    INCREASE_CPU_REQUEST      = "INCREASE_CPU_REQUEST"
    INVESTIGATE_APPLICATION   = "INVESTIGATE_APPLICATION"
    CHECK_NODE_UTILIZATION    = "CHECK_NODE_UTILIZATION"
    RESTART_POD               = "RESTART_POD"
    REVIEW_DEPLOYMENT         = "REVIEW_DEPLOYMENT"
    MONITOR_CLOSELY           = "MONITOR_CLOSELY"
    NO_ACTION_REQUIRED        = "NO_ACTION_REQUIRED"

"""
ActionType Enum — Phase 8.

Defines the specific types of actions the Action Planner can prescribe.
Used to ensure deterministic parsing and downstream execution.
"""
from enum import Enum


class ActionType(str, Enum):
    KUBECTL_COMMAND      = "KUBECTL_COMMAND"
    PATCH_DEPLOYMENT     = "PATCH_DEPLOYMENT"
    HELM_UPGRADE         = "HELM_UPGRADE"
    MANUAL_INVESTIGATION = "MANUAL_INVESTIGATION"
    CREATE_TICKET        = "CREATE_TICKET"
    NO_ACTION            = "NO_ACTION"

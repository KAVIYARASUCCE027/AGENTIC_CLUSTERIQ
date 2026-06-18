"""
Execution Policy Enum — Phase 10.
"""
from enum import Enum

class ExecutionPolicy(str, Enum):
    SEQUENTIAL  = "SEQUENTIAL"
    PARALLEL    = "PARALLEL"
    CONDITIONAL = "CONDITIONAL"

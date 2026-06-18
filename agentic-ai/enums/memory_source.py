"""
MemorySource Enum — Phase 9.

Indicates where a historical memory block was retrieved from.
Allows the system to gracefully degrade if the database goes down.
"""
from enum import Enum


class MemorySource(str, Enum):
    MONGODB         = "MONGODB"
    IN_MEMORY_CACHE = "IN_MEMORY_CACHE"
    FALLBACK        = "FALLBACK"

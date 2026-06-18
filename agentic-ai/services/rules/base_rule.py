from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field

from schemas.cpu_state import CPUState
from schemas.analyzer_output import HealthStatus, Severity, AbnormalityType

class RuleResult(BaseModel):
    """
    Structured output returned by an individual rule.
    """
    status: Optional[HealthStatus] = None
    severity: Optional[Severity] = None
    abnormality: Optional[AbnormalityType] = None
    root_cause: Optional[str] = None
    trend: Optional[str] = None
    reasoning: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    action_plan: List[str] = Field(default_factory=list)
    confidence_score: int = Field(default=0)

class BaseRule(ABC):
    """
    Abstract base class for all analyzer rules.
    """
    
    @abstractmethod
    def evaluate(self, state: CPUState) -> RuleResult:
        """
        Evaluate the rule against the current CPUState.
        Returns a RuleResult with insights and confidence.
        """
        pass

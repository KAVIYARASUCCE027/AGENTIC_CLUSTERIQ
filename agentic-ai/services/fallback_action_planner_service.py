"""
Fallback Action Planner Service — Phase 8.

Provides deterministic rule-based action plans when:
  - Gemini API is unavailable or fails all retries
  - Gemini returns confidence < 60
  - Invalid response received

Rules map primary RecommendationType to executable steps.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from enums.action_type import ActionType
from enums.action_priority import ActionPriority
from enums.action_risk import ActionRisk
from enums.action_source import ActionSource
from enums.recommendation_type import RecommendationType
from schemas.action_plan_input import ActionPlanInputSchema
from schemas.action_plan_output import ActionPlanOutputState, ActionStep
from utils.action_planner_logger import ActionPlannerLogger

logger = logging.getLogger(__name__)
plan_logger = ActionPlannerLogger("services.fallback_action_planner_service")


def _build_plan_for_recommendation(rec: RecommendationType, namespace: str, pod_name: str) -> ActionPlanOutputState:
    """Builds a deterministic plan based on a given recommendation."""
    
    if rec == RecommendationType.INCREASE_CPU_LIMIT:
        return ActionPlanOutputState(
            actions=[
                ActionStep(
                    step=1,
                    action=f"Identify the deployment managing pod {pod_name} in {namespace}.",
                    action_type=ActionType.KUBECTL_COMMAND,
                    risk=ActionRisk.LOW,
                    estimated_duration="1 minute"
                ),
                ActionStep(
                    step=2,
                    action="Patch the deployment to increase the CPU limit by 20%.",
                    action_type=ActionType.PATCH_DEPLOYMENT,
                    risk=ActionRisk.MEDIUM,
                    estimated_duration="2 minutes"
                )
            ],
            priority=ActionPriority.HIGH,
            risk=ActionRisk.MEDIUM,
            estimated_duration="3 minutes",
            rollback_strategy="Revert the deployment CPU limit to its previous value.",
            confidence=85,
            source=ActionSource.FALLBACK,
            model_name="fallback"
        )
        
    if rec == RecommendationType.SCALE_UP_REPLICAS:
        return ActionPlanOutputState(
            actions=[
                ActionStep(
                    step=1,
                    action=f"Scale up the deployment managing pod {pod_name} by adding 1-2 replicas.",
                    action_type=ActionType.KUBECTL_COMMAND,
                    risk=ActionRisk.LOW,
                    estimated_duration="1 minute"
                )
            ],
            priority=ActionPriority.HIGH,
            risk=ActionRisk.LOW,
            estimated_duration="1 minute",
            rollback_strategy="Scale down the deployment back to the original replica count.",
            confidence=85,
            source=ActionSource.FALLBACK,
            model_name="fallback"
        )

    if rec == RecommendationType.ENABLE_HPA:
        return ActionPlanOutputState(
            actions=[
                ActionStep(
                    step=1,
                    action=f"Create or configure HPA for the deployment managing {pod_name}.",
                    action_type=ActionType.KUBECTL_COMMAND,
                    risk=ActionRisk.MEDIUM,
                    estimated_duration="3 minutes"
                )
            ],
            priority=ActionPriority.MEDIUM,
            risk=ActionRisk.MEDIUM,
            estimated_duration="3 minutes",
            rollback_strategy="Delete the HPA resource or revert its configuration.",
            confidence=80,
            source=ActionSource.FALLBACK,
            model_name="fallback"
        )
        
    if rec == RecommendationType.RESTART_POD:
        return ActionPlanOutputState(
            actions=[
                ActionStep(
                    step=1,
                    action=f"Delete pod {pod_name} in {namespace} to force a restart.",
                    action_type=ActionType.KUBECTL_COMMAND,
                    risk=ActionRisk.MEDIUM,
                    estimated_duration="1 minute"
                )
            ],
            priority=ActionPriority.HIGH,
            risk=ActionRisk.MEDIUM,
            estimated_duration="1 minute",
            rollback_strategy="If the new pod fails to start, investigate image or config issues. Cannot strictly rollback a pod delete.",
            confidence=80,
            source=ActionSource.FALLBACK,
            model_name="fallback"
        )
        
    if rec == RecommendationType.INVESTIGATE_APPLICATION:
        return ActionPlanOutputState(
            actions=[
                ActionStep(
                    step=1,
                    action=f"Fetch logs for pod {pod_name} in {namespace} (previous and current).",
                    action_type=ActionType.KUBECTL_COMMAND,
                    risk=ActionRisk.LOW,
                    estimated_duration="2 minutes"
                ),
                ActionStep(
                    step=2,
                    action="Create a Jira/ServiceNow ticket for the application team to review the logs.",
                    action_type=ActionType.CREATE_TICKET,
                    risk=ActionRisk.LOW,
                    estimated_duration="5 minutes"
                )
            ],
            priority=ActionPriority.MEDIUM,
            risk=ActionRisk.LOW,
            estimated_duration="7 minutes",
            rollback_strategy="Close the ticket if determined to be a false alarm.",
            confidence=80,
            source=ActionSource.FALLBACK,
            model_name="fallback"
        )

    # Default fallback plan for other recommendations or NO_ACTION
    return ActionPlanOutputState(
        actions=[
            ActionStep(
                step=1,
                action=f"Monitor pod {pod_name} closely.",
                action_type=ActionType.MANUAL_INVESTIGATION,
                risk=ActionRisk.LOW,
                estimated_duration="Ongoing"
            )
        ],
        priority=ActionPriority.LOW,
        risk=ActionRisk.LOW,
        estimated_duration="Unknown",
        rollback_strategy="N/A",
        confidence=50,
        source=ActionSource.FALLBACK,
        model_name="fallback"
    )


class FallbackActionPlannerService:
    """
    Deterministic fallback action planner service.
    Takes the highest priority recommendation and produces a runbook.
    """

    def plan_action(self, inp: ActionPlanInputSchema) -> ActionPlanOutputState:
        recs = inp.recommendation_output.recommendations
        
        primary_rec = recs[0] if recs else RecommendationType.NO_ACTION_REQUIRED
        
        plan = _build_plan_for_recommendation(primary_rec, inp.namespace, inp.pod_name)

        plan_logger.log_fallback_triggered(f"primary_rec={primary_rec.value}")
        plan_logger.log_parsed_output(
            len(plan.actions),
            plan.confidence,
            ActionSource.FALLBACK.value
        )

        return plan

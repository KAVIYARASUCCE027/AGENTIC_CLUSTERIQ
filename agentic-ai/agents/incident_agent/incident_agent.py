import logging
from datetime import datetime, timezone
import uuid

from schemas.cpu_state import CPUState
from schemas.incident_input import IncidentInput
from schemas.incident_output import IncidentOutput
from schemas.enums.incident_severity import IncidentSeverity
from services.incident_service import IncidentService
from schemas.event_message import EventMessage
from config.event_types import EventType
from services.global_bus import subscriber

logger = logging.getLogger(__name__)

class IncidentAgent:
    """
    Incident Agent — Phase 19.
    Groups correlated events into incidents and tracks their lifecycle.
    """
    def __init__(self):
        self._incident_service = IncidentService()
        # Subscribe to correlated events
        subscriber.subscribe(EventType.RESOURCE_EXHAUSTION, self.handle_event)
        subscriber.subscribe(EventType.APPLICATION_OVERLOAD, self.handle_event)
        subscriber.subscribe(EventType.NODE_FAILURE, self.handle_event)

    @property
    def name(self) -> str:
        return "IncidentAgent"

    def execute(self, state: CPUState) -> CPUState:
        logger.info(f"{self.name}: Processing incident creation...")

        # We need correlation output to create an incident
        if not state.correlation_output:
            logger.warning(f"{self.name}: No correlation output found. Skipping incident creation.")
            return state

        # Generate Incident ID
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        short_uuid = str(uuid.uuid4())[:4].upper()
        incident_id = f"INC-{date_str}-{short_uuid}"

        # Build title
        pod_name = state.inputs.pod_name
        incident_type_str = state.correlation_output.incident_type.value.replace("_", " ").title()
        title = f"{incident_type_str} on {pod_name}"

        description = state.correlation_output.correlation_summary
        
        # Determine Severity based on Confidence Score or default
        severity = IncidentSeverity.MEDIUM
        if state.correlation_output.confidence_score > 0.8:
            severity = IncidentSeverity.HIGH
        if state.correlation_output.confidence_score > 0.95:
            severity = IncidentSeverity.CRITICAL

        # Prepare input
        inputs = IncidentInput(
            pod_name=pod_name,
            namespace=state.inputs.namespace,
            related_events=state.correlation_output.correlated_events
        )

        # Create Incident
        incident = self._incident_service.create_incident(
            incident_id=incident_id,
            title=title,
            description=description,
            severity=severity,
            inputs=inputs
        )
        
        logger.info(f"[{self.name}] Created incident {incident_id}")

        # Update state
        state.incident_output = IncidentOutput(
            incident_id=incident.incident_id,
            incident_status=incident.status,
            incident_severity=incident.severity
        )

        return state

    async def handle_event(self, event: EventMessage):
        """Async event handler for Event Bus interactions."""
        logger.info(f"[{self.name}] Received correlated event via EventBus: {event.event_type}")
        # Could dynamically trigger incident creation from event here in async flows
        pass

import logging
from typing import List, Optional
from datetime import datetime, timezone

from repositories.incident_repository import IncidentRepository
from schemas.incident_schema import IncidentSchema
from schemas.incident_history_schema import IncidentHistorySchema
from schemas.incident_input import IncidentInput
from schemas.enums.incident_status import IncidentStatus
from schemas.enums.incident_severity import IncidentSeverity

from services.global_bus import publisher
from config.event_types import EventType

logger = logging.getLogger(__name__)

class IncidentService:
    def __init__(self):
        self._repo = IncidentRepository()

    def create_incident(self, incident_id: str, title: str, description: str, severity: IncidentSeverity, inputs: IncidentInput) -> IncidentSchema:
        incident = IncidentSchema(
            incident_id=incident_id,
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.OPEN,
            root_cause=inputs.root_cause,
            recommendation=inputs.recommendation,
            pod_name=inputs.pod_name,
            namespace=inputs.namespace,
            related_events=inputs.related_events,
            resource_type="COMPOSITE",
        )
        saved = self._repo.save_incident(incident)
        
        # Publish event
        publisher.publish_sync(
            publisher.create_event(
                event_type=EventType.INCIDENT_CREATED,
                source="IncidentService",
                payload={"incident_id": incident_id, "title": title, "severity": severity.value}
            )
        )
        return saved

    def acknowledge_incident(self, incident_id: str, acknowledged_by: str) -> bool:
        incident = self._repo.find_by_id(incident_id)
        if not incident:
            return False
            
        previous_status = incident.status
        if previous_status == IncidentStatus.ACKNOWLEDGED:
            return True
            
        success = self._repo.update_status(incident_id, IncidentStatus.ACKNOWLEDGED)
        if success:
            history = IncidentHistorySchema(
                incident_id=incident_id,
                previous_status=previous_status,
                new_status=IncidentStatus.ACKNOWLEDGED,
                previous_severity=incident.severity,
                new_severity=incident.severity,
                changed_by=acknowledged_by
            )
            self._repo.save_history(history)
            
            publisher.publish_sync(
                publisher.create_event(
                    event_type=EventType.INCIDENT_ACKNOWLEDGED,
                    source="IncidentService",
                    payload={"incident_id": incident_id, "acknowledged_by": acknowledged_by}
                )
            )
        return success

    def resolve_incident(self, incident_id: str, resolved_by: str) -> bool:
        incident = self._repo.find_by_id(incident_id)
        if not incident:
            return False
            
        previous_status = incident.status
        success = self._repo.update_status(incident_id, IncidentStatus.RESOLVED)
        if success:
            history = IncidentHistorySchema(
                incident_id=incident_id,
                previous_status=previous_status,
                new_status=IncidentStatus.RESOLVED,
                previous_severity=incident.severity,
                new_severity=incident.severity,
                changed_by=resolved_by
            )
            self._repo.save_history(history)
            
            publisher.publish_sync(
                publisher.create_event(
                    event_type=EventType.INCIDENT_RESOLVED,
                    source="IncidentService",
                    payload={"incident_id": incident_id, "resolved_by": resolved_by}
                )
            )
        return success

    def escalate_severity(self, incident_id: str, new_severity: IncidentSeverity, escalated_by: str) -> bool:
        incident = self._repo.find_by_id(incident_id)
        if not incident:
            return False
            
        previous_severity = incident.severity
        if previous_severity == new_severity:
            return True
            
        success = self._repo.update_severity(incident_id, new_severity)
        if success:
            history = IncidentHistorySchema(
                incident_id=incident_id,
                previous_status=incident.status,
                new_status=incident.status,
                previous_severity=previous_severity,
                new_severity=new_severity,
                changed_by=escalated_by
            )
            self._repo.save_history(history)
            
            publisher.publish_sync(
                publisher.create_event(
                    event_type=EventType.INCIDENT_ESCALATED,
                    source="IncidentService",
                    payload={"incident_id": incident_id, "previous_severity": previous_severity.value, "new_severity": new_severity.value}
                )
            )
        return success

    def get_incident(self, incident_id: str) -> Optional[IncidentSchema]:
        return self._repo.find_by_id(incident_id)

    def list_open_incidents(self) -> List[IncidentSchema]:
        return self._repo.find_open_incidents()

    def list_resolved_incidents(self) -> List[IncidentSchema]:
        return self._repo.find_resolved_incidents()

    def get_incident_history(self, incident_id: str) -> List[IncidentHistorySchema]:
        return self._repo.find_history(incident_id)

"""Event collector for NyxAI.

This module provides event collection and storage functionality,
with support for PostgreSQL persistence using SQLAlchemy.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Index,
    String,
    Text,
    select,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

Base = declarative_base()


class EventType(StrEnum):
    """Types of system events."""

    ALERT = "alert"
    ANOMALY = "anomaly"
    DEPLOYMENT = "deployment"
    INCIDENT = "incident"
    MAINTENANCE = "maintenance"
    METRIC_THRESHOLD = "metric_threshold"
    SYSTEM = "system"
    CUSTOM = "custom"


class EventStatus(StrEnum):
    """Status of an event."""

    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    ESCALATED = "escalated"


class EventSeverity(StrEnum):
    """Severity levels for events."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EventModelDB(Base):
    """SQLAlchemy model for events table."""

    __tablename__ = "events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    status = Column(
        SQLEnum(EventStatus),
        nullable=False,
        default=EventStatus.PENDING,
        index=True,
    )
    severity = Column(SQLEnum(EventSeverity), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(128), nullable=False, index=True)
    service = Column(String(128), nullable=True, index=True)
    host = Column(String(128), nullable=True, index=True)
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    acknowledged_by = Column(String(128), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_events_created_at", "created_at"),
        Index("ix_events_service_created", "service", "created_at"),
        Index("ix_events_type_severity", "event_type", "severity"),
    )


class EventModel(BaseModel):
    """Pydantic model for event data validation.

    Attributes:
        id: Unique event identifier
        event_type: Type of event
        status: Current status of the event
        severity: Severity level
        title: Short event title
        description: Detailed event description
        source: Source system that generated the event
        service: Optional service name
        host: Optional host name
        metadata: Additional structured data
        tags: List of tags for categorization
        acknowledged_by: User who acknowledged the event
        acknowledged_at: When the event was acknowledged
        resolved_at: When the event was resolved
        created_at: When the event was created
        updated_at: When the event was last updated
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    status: EventStatus = EventStatus.PENDING
    severity: EventSeverity
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    source: str = Field(..., min_length=1, max_length=128)
    service: str | None = Field(default=None, max_length=128)
    host: str | None = Field(default=None, max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    acknowledged_by: str | None = Field(default=None, max_length=128)
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_db_model(self) -> EventModelDB:
        """Convert to SQLAlchemy model."""
        return EventModelDB(
            id=self.id,
            event_type=self.event_type,
            status=self.status,
            severity=self.severity,
            title=self.title,
            description=self.description,
            source=self.source,
            service=self.service,
            host=self.host,
            metadata=self.metadata,
            tags=self.tags,
            acknowledged_by=self.acknowledged_by,
            acknowledged_at=self.acknowledged_at,
            resolved_at=self.resolved_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_db_model(cls, db_model: EventModelDB) -> EventModel:
        """Create from SQLAlchemy model."""
        return cls.model_validate(db_model)

    def acknowledge(self, user: str) -> None:
        """Mark event as acknowledged.

        Args:
            user: User acknowledging the event
        """
        self.status = EventStatus.ACKNOWLEDGED
        self.acknowledged_by = user
        self.acknowledged_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def resolve(self) -> None:
        """Mark event as resolved."""
        self.status = EventStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def escalate(self) -> None:
        """Escalate the event."""
        self.status = EventStatus.ESCALATED
        self.updated_at = datetime.utcnow()

    def suppress(self) -> None:
        """Suppress the event."""
        self.status = EventStatus.SUPPRESSED
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the event.

        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the event.

        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()

    def update_metadata(self, key: str, value: Any) -> None:
        """Update metadata field.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()


class EventFilter(BaseModel):
    """Filter criteria for event queries.

    Attributes:
        event_types: Filter by event types
        statuses: Filter by statuses
        severities: Filter by severity levels
        source: Filter by source
        service: Filter by service
        host: Filter by host
        tags: Filter by tags (all must match)
        start_time: Filter events created after this time
        end_time: Filter events created before this time
        search_query: Search in title and description
    """

    event_types: list[EventType] | None = None
    statuses: list[EventStatus] | None = None
    severities: list[EventSeverity] | None = None
    source: str | None = None
    service: str | None = None
    host: str | None = None
    tags: list[str] | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    search_query: str | None = None


class EventCollector:
    """Collector for system events with PostgreSQL storage.

    This collector provides CRUD operations for events with support for
    filtering, pagination, and aggregation.

    Example:
        >>> collector = EventCollector(session)
        >>> # Create an event
        >>> event = await collector.create_event(EventModel(
        ...     event_type=EventType.ALERT,
        ...     severity=EventSeverity.HIGH,
        ...     title="High CPU Usage",
        ...     source="prometheus",
        ...     service="api-server"
        ... ))
        >>> # Query events
        >>> events = await collector.get_events(
        ...     filter=EventFilter(severities=[EventSeverity.HIGH])
        ... )
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the event collector.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create_event(self, event: EventModel) -> EventModel:
        """Create a new event.

        Args:
            event: Event to create

        Returns:
            Created event with assigned ID
        """
        db_event = event.to_db_model()
        self.session.add(db_event)
        await self.session.commit()
        await self.session.refresh(db_event)
        return EventModel.from_db_model(db_event)

    async def get_event(self, event_id: UUID) -> EventModel | None:
        """Get a single event by ID.

        Args:
            event_id: Event UUID

        Returns:
            Event if found, None otherwise
        """
        result = await self.session.execute(
            select(EventModelDB).where(EventModelDB.id == event_id)
        )
        db_event = result.scalar_one_or_none()
        if db_event is None:
            return None
        return EventModel.from_db_model(db_event)

    async def get_events(
        self,
        filter_criteria: EventFilter | None = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        descending: bool = True,
    ) -> list[EventModel]:
        """Get events with optional filtering.

        Args:
            filter_criteria: Optional filter criteria
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field to order by
            descending: Sort in descending order

        Returns:
            List of matching events
        """
        query = select(EventModelDB)

        if filter_criteria:
            query = self._apply_filters(query, filter_criteria)

        # Apply ordering
        order_column = getattr(EventModelDB, order_by, EventModelDB.created_at)
        if descending:
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        # Apply pagination
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        db_events = result.scalars().all()
        return [EventModel.from_db_model(e) for e in db_events]

    async def count_events(
        self,
        filter_criteria: EventFilter | None = None,
    ) -> int:
        """Count events matching filter criteria.

        Args:
            filter_criteria: Optional filter criteria

        Returns:
            Number of matching events
        """
        from sqlalchemy import func

        query = select(func.count(EventModelDB.id))

        if filter_criteria:
            query = self._apply_filters(query, filter_criteria)

        result = await self.session.execute(query)
        return result.scalar() or 0

    def _apply_filters(
        self,
        query: Any,
        filter_criteria: EventFilter,
    ) -> Any:
        """Apply filter criteria to query.

        Args:
            query: Base query
            filter_criteria: Filter criteria

        Returns:
            Modified query with filters applied
        """
        if filter_criteria.event_types:
            query = query.where(
                EventModelDB.event_type.in_(filter_criteria.event_types)
            )

        if filter_criteria.statuses:
            query = query.where(EventModelDB.status.in_(filter_criteria.statuses))

        if filter_criteria.severities:
            query = query.where(
                EventModelDB.severity.in_(filter_criteria.severities)
            )

        if filter_criteria.source:
            query = query.where(EventModelDB.source == filter_criteria.source)

        if filter_criteria.service:
            query = query.where(EventModelDB.service == filter_criteria.service)

        if filter_criteria.host:
            query = query.where(EventModelDB.host == filter_criteria.host)

        if filter_criteria.start_time:
            query = query.where(EventModelDB.created_at >= filter_criteria.start_time)

        if filter_criteria.end_time:
            query = query.where(EventModelDB.created_at <= filter_criteria.end_time)

        if filter_criteria.tags:
            # Check if all specified tags are present
            for tag in filter_criteria.tags:
                query = query.where(EventModelDB.tags.contains([tag]))

        if filter_criteria.search_query:
            search = f"%{filter_criteria.search_query}%"
            query = query.where(
                (EventModelDB.title.ilike(search))
                | (EventModelDB.description.ilike(search))
            )

        return query

    async def update_event(self, event: EventModel) -> EventModel:
        """Update an existing event.

        Args:
            event: Event to update

        Returns:
            Updated event
        """
        db_event = event.to_db_model()
        db_event.updated_at = datetime.utcnow()
        await self.session.merge(db_event)
        await self.session.commit()
        return event

    async def delete_event(self, event_id: UUID) -> bool:
        """Delete an event.

        Args:
            event_id: Event UUID to delete

        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            select(EventModelDB).where(EventModelDB.id == event_id)
        )
        db_event = result.scalar_one_or_none()
        if db_event is None:
            return False

        await self.session.delete(db_event)
        await self.session.commit()
        return True

    async def acknowledge_event(
        self,
        event_id: UUID,
        user: str,
    ) -> EventModel | None:
        """Acknowledge an event.

        Args:
            event_id: Event UUID
            user: User acknowledging the event

        Returns:
            Updated event if found, None otherwise
        """
        event = await self.get_event(event_id)
        if event is None:
            return None

        event.acknowledge(user)
        return await self.update_event(event)

    async def resolve_event(self, event_id: UUID) -> EventModel | None:
        """Resolve an event.

        Args:
            event_id: Event UUID

        Returns:
            Updated event if found, None otherwise
        """
        event = await self.get_event(event_id)
        if event is None:
            return None

        event.resolve()
        return await self.update_event(event)

    async def escalate_event(self, event_id: UUID) -> EventModel | None:
        """Escalate an event.

        Args:
            event_id: Event UUID

        Returns:
            Updated event if found, None otherwise
        """
        event = await self.get_event(event_id)
        if event is None:
            return None

        event.escalate()
        return await self.update_event(event)

    async def get_active_events(
        self,
        service: str | None = None,
        severity: EventSeverity | None = None,
    ) -> list[EventModel]:
        """Get active (non-resolved, non-suppressed) events.

        Args:
            service: Optional service filter
            severity: Optional severity filter

        Returns:
            List of active events
        """
        filter_criteria = EventFilter(
            statuses=[EventStatus.PENDING, EventStatus.ACKNOWLEDGED, EventStatus.ESCALATED],
        )

        if service:
            filter_criteria.service = service
        if severity:
            filter_criteria.severities = [severity]

        return await self.get_events(filter_criteria=filter_criteria, limit=1000)

    async def get_event_stats(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Get event statistics.

        Args:
            start_time: Optional start time for stats
            end_time: Optional end time for stats

        Returns:
            Dictionary of statistics
        """
        from sqlalchemy import func

        query = select(
            EventModelDB.event_type,
            EventModelDB.status,
            EventModelDB.severity,
            func.count(EventModelDB.id).label("count"),
        )

        if start_time:
            query = query.where(EventModelDB.created_at >= start_time)
        if end_time:
            query = query.where(EventModelDB.created_at <= end_time)

        query = query.group_by(
            EventModelDB.event_type,
            EventModelDB.status,
            EventModelDB.severity,
        )

        result = await self.session.execute(query)
        rows = result.all()

        stats = {
            "by_type": {},
            "by_status": {},
            "by_severity": {},
            "total": 0,
        }

        for row in rows:
            event_type, status, severity, count = row
            stats["total"] += count

            type_key = event_type.value if event_type else "unknown"
            status_key = status.value if status else "unknown"
            severity_key = severity.value if severity else "unknown"

            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + count
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + count
            stats["by_severity"][severity_key] = (
                stats["by_severity"].get(severity_key, 0) + count
            )

        return stats

    async def bulk_create_events(self, events: list[EventModel]) -> list[EventModel]:
        """Create multiple events in bulk.

        Args:
            events: List of events to create

        Returns:
            List of created events
        """
        db_events = [event.to_db_model() for event in events]
        self.session.add_all(db_events)
        await self.session.commit()

        # Refresh all events to get their IDs
        for db_event in db_events:
            await self.session.refresh(db_event)

        return [EventModel.from_db_model(e) for e in db_events]

    async def create_from_alert(
        self,
        alert_name: str,
        alert_labels: dict[str, str],
        alert_annotations: dict[str, str],
        severity: EventSeverity = EventSeverity.MEDIUM,
    ) -> EventModel:
        """Create an event from a Prometheus-style alert.

        Args:
            alert_name: Name of the alert
            alert_labels: Alert labels
            alert_annotations: Alert annotations
            severity: Event severity

        Returns:
            Created event
        """
        event = EventModel(
            event_type=EventType.ALERT,
            severity=severity,
            title=alert_annotations.get("summary", alert_name),
            description=alert_annotations.get("description", ""),
            source="prometheus",
            service=alert_labels.get("service") or alert_labels.get("job"),
            host=(
                alert_labels.get("instance", "").split(":")[0]
                if alert_labels.get("instance")
                else None
            ),
            metadata={
                "alert_name": alert_name,
                "labels": alert_labels,
                "annotations": alert_annotations,
            },
            tags=list(alert_labels.keys()),
        )

        return await self.create_event(event)

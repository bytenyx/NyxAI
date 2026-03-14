"""Data enrichment module for NyxAI.

This module provides data enrichment capabilities to add context
and metadata to collected data for better analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from nyxai.config import settings

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class EnrichmentConfig:
    """Configuration for data enrichment.

    Attributes:
        add_geolocation: Whether to add geolocation data
        add_service_metadata: Whether to add service metadata
        add_host_metadata: Whether to add host metadata
        add_temporal_features: Whether to add temporal features
        add_derived_metrics: Whether to add derived metrics
        enrichment_timeout: Timeout for external enrichment calls
        custom_enrichers: List of custom enrichment functions
    """

    add_geolocation: bool = False
    add_service_metadata: bool = True
    add_host_metadata: bool = True
    add_temporal_features: bool = True
    add_derived_metrics: bool = True
    enrichment_timeout: int = 10
    custom_enrichers: list[Callable[[dict[str, Any]], dict[str, Any]]] = field(
        default_factory=list
    )


@dataclass
class EnrichmentResult:
    """Result of data enrichment.

    Attributes:
        data: Enriched data
        enriched_fields: List of fields that were added
        errors: List of errors encountered during enrichment
        processing_time_ms: Time taken to enrich in milliseconds
    """

    data: dict[str, Any] = field(default_factory=dict)
    enriched_fields: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    processing_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "data": self.data,
            "enriched_fields": self.enriched_fields,
            "errors": self.errors,
            "processing_time_ms": self.processing_time_ms,
        }


class ServiceMetadata(BaseModel):
    """Service metadata model.

    Attributes:
        name: Service name
        version: Service version
        environment: Deployment environment
        team: Owning team
        repository: Code repository URL
        documentation: Documentation URL
        dependencies: List of service dependencies
    """

    model_config = ConfigDict(extra="allow")

    name: str
    version: str | None = None
    environment: str | None = None
    team: str | None = None
    repository: str | None = None
    documentation: str | None = None
    dependencies: list[str] = Field(default_factory=list)


class HostMetadata(BaseModel):
    """Host metadata model.

    Attributes:
        hostname: Host name
        ip_address: IP address
        os: Operating system
        os_version: OS version
        architecture: System architecture
        region: Cloud region
        zone: Availability zone
        instance_type: Instance/machine type
        tags: Host tags
    """

    model_config = ConfigDict(extra="allow")

    hostname: str
    ip_address: str | None = None
    os: str | None = None
    os_version: str | None = None
    architecture: str | None = None
    region: str | None = None
    zone: str | None = None
    instance_type: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class TemporalFeatures(BaseModel):
    """Temporal features extracted from timestamps.

    Attributes:
        hour: Hour of day (0-23)
        day_of_week: Day of week (0-6, Monday=0)
        day_of_month: Day of month (1-31)
        month: Month (1-12)
        year: Year
        is_weekend: Whether it's a weekend
        is_business_hours: Whether it's business hours (9-17)
        quarter: Quarter of year (1-4)
    """

    model_config = ConfigDict(extra="allow")

    hour: int
    day_of_week: int
    day_of_month: int
    month: int
    year: int
    is_weekend: bool
    is_business_hours: bool
    quarter: int

    @classmethod
    def from_timestamp(cls, timestamp: datetime) -> TemporalFeatures:
        """Create temporal features from a timestamp.

        Args:
            timestamp: Datetime to extract features from

        Returns:
            TemporalFeatures instance
        """
        return cls(
            hour=timestamp.hour,
            day_of_week=timestamp.weekday(),
            day_of_month=timestamp.day,
            month=timestamp.month,
            year=timestamp.year,
            is_weekend=timestamp.weekday() >= 5,
            is_business_hours=9 <= timestamp.hour < 17 and timestamp.weekday() < 5,
            quarter=(timestamp.month - 1) // 3 + 1,
        )


class DataEnricher:
    """Data enricher for NyxAI collectors.

    This class provides methods to enrich various data types
    with additional context and metadata.

    Example:
        >>> enricher = DataEnricher()
        >>> # Enrich metric data
        >>> result = enricher.enrich_metric(metric_data)
        >>> # Enrich log data
        >>> result = enricher.enrich_log(log_data)
    """

    def __init__(self, config: EnrichmentConfig | None = None) -> None:
        """Initialize the data enricher.

        Args:
            config: Enrichment configuration
        """
        self.config = config or EnrichmentConfig()
        self._service_cache: dict[str, ServiceMetadata] = {}
        self._host_cache: dict[str, HostMetadata] = {}

    async def enrich_metric(self, metric: dict[str, Any]) -> EnrichmentResult:
        """Enrich metric data with additional context.

        Args:
            metric: Metric data to enrich

        Returns:
            Enrichment result
        """
        import time

        start_time = time.time()
        result = EnrichmentResult(data=dict(metric))
        enriched_fields = []

        try:
            # Add temporal features
            if self.config.add_temporal_features:
                timestamp = metric.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if isinstance(timestamp, datetime):
                        temporal = TemporalFeatures.from_timestamp(timestamp)
                        result.data["temporal"] = temporal.model_dump()
                        enriched_fields.append("temporal")

            # Add service metadata
            if self.config.add_service_metadata:
                service = metric.get("labels", {}).get("service") or metric.get("service")
                if service and service not in self._service_cache:
                    metadata = await self._fetch_service_metadata(service)
                    if metadata:
                        self._service_cache[service] = metadata
                        result.data["service_metadata"] = metadata.model_dump()
                        enriched_fields.append("service_metadata")
                elif service and service in self._service_cache:
                    result.data["service_metadata"] = self._service_cache[service].model_dump()
                    enriched_fields.append("service_metadata")

            # Add host metadata
            if self.config.add_host_metadata:
                host = metric.get("labels", {}).get("instance") or metric.get("host")
                if host:
                    hostname = host.split(":")[0] if ":" in host else host
                    if hostname not in self._host_cache:
                        metadata = await self._fetch_host_metadata(hostname)
                        if metadata:
                            self._host_cache[hostname] = metadata
                            result.data["host_metadata"] = metadata.model_dump()
                            enriched_fields.append("host_metadata")
                    else:
                        result.data["host_metadata"] = self._host_cache[hostname].model_dump()
                        enriched_fields.append("host_metadata")

            # Add derived metrics
            if self.config.add_derived_metrics:
                derived = self._calculate_derived_metrics(metric)
                if derived:
                    result.data["derived"] = derived
                    enriched_fields.append("derived")

            # Apply custom enrichers
            for enricher in self.config.custom_enrichers:
                try:
                    result.data = enricher(result.data)
                    enriched_fields.append(f"custom_{enricher.__name__}")
                except Exception as e:
                    result.errors.append(f"Custom enricher failed: {e}")

        except Exception as e:
            result.errors.append(f"Enrichment failed: {e}")

        result.enriched_fields = enriched_fields
        result.processing_time_ms = (time.time() - start_time) * 1000

        return result

    async def enrich_log(self, log: dict[str, Any]) -> EnrichmentResult:
        """Enrich log data with additional context.

        Args:
            log: Log data to enrich

        Returns:
            Enrichment result
        """
        import time

        start_time = time.time()
        result = EnrichmentResult(data=dict(log))
        enriched_fields = []

        try:
            # Add temporal features
            if self.config.add_temporal_features:
                timestamp = log.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if isinstance(timestamp, datetime):
                        temporal = TemporalFeatures.from_timestamp(timestamp)
                        result.data["temporal"] = temporal.model_dump()
                        enriched_fields.append("temporal")

            # Add service metadata
            if self.config.add_service_metadata:
                service = log.get("service")
                if service and service not in self._service_cache:
                    metadata = await self._fetch_service_metadata(service)
                    if metadata:
                        self._service_cache[service] = metadata
                        result.data["service_metadata"] = metadata.model_dump()
                        enriched_fields.append("service_metadata")
                elif service and service in self._service_cache:
                    result.data["service_metadata"] = self._service_cache[service].model_dump()
                    enriched_fields.append("service_metadata")

            # Add host metadata
            if self.config.add_host_metadata:
                host = log.get("host")
                if host:
                    if host not in self._host_cache:
                        metadata = await self._fetch_host_metadata(host)
                        if metadata:
                            self._host_cache[host] = metadata
                            result.data["host_metadata"] = metadata.model_dump()
                            enriched_fields.append("host_metadata")
                    else:
                        result.data["host_metadata"] = self._host_cache[host].model_dump()
                        enriched_fields.append("host_metadata")

            # Parse log message for patterns
            message = log.get("message", "")
            if message:
                patterns = self._extract_log_patterns(message)
                if patterns:
                    result.data["patterns"] = patterns
                    enriched_fields.append("patterns")

            # Apply custom enrichers
            for enricher in self.config.custom_enrichers:
                try:
                    result.data = enricher(result.data)
                    enriched_fields.append(f"custom_{enricher.__name__}")
                except Exception as e:
                    result.errors.append(f"Custom enricher failed: {e}")

        except Exception as e:
            result.errors.append(f"Enrichment failed: {e}")

        result.enriched_fields = enriched_fields
        result.processing_time_ms = (time.time() - start_time) * 1000

        return result

    async def enrich_event(self, event: dict[str, Any]) -> EnrichmentResult:
        """Enrich event data with additional context.

        Args:
            event: Event data to enrich

        Returns:
            Enrichment result
        """
        import time

        start_time = time.time()
        result = EnrichmentResult(data=dict(event))
        enriched_fields = []

        try:
            # Add temporal features
            if self.config.add_temporal_features:
                timestamp = event.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if isinstance(timestamp, datetime):
                        temporal = TemporalFeatures.from_timestamp(timestamp)
                        result.data["temporal"] = temporal.model_dump()
                        enriched_fields.append("temporal")

            # Add service metadata
            if self.config.add_service_metadata:
                service = event.get("service")
                if service and service not in self._service_cache:
                    metadata = await self._fetch_service_metadata(service)
                    if metadata:
                        self._service_cache[service] = metadata
                        result.data["service_metadata"] = metadata.model_dump()
                        enriched_fields.append("service_metadata")
                elif service and service in self._service_cache:
                    result.data["service_metadata"] = self._service_cache[service].model_dump()
                    enriched_fields.append("service_metadata")

            # Add host metadata
            if self.config.add_host_metadata:
                host = event.get("host")
                if host:
                    if host not in self._host_cache:
                        metadata = await self._fetch_host_metadata(host)
                        if metadata:
                            self._host_cache[host] = metadata
                            result.data["host_metadata"] = metadata.model_dump()
                            enriched_fields.append("host_metadata")
                    else:
                        result.data["host_metadata"] = self._host_cache[host].model_dump()
                        enriched_fields.append("host_metadata")

            # Add related events correlation
            if event.get("metadata"):
                correlation = self._extract_correlation_info(event)
                if correlation:
                    result.data["correlation"] = correlation
                    enriched_fields.append("correlation")

            # Apply custom enrichers
            for enricher in self.config.custom_enrichers:
                try:
                    result.data = enricher(result.data)
                    enriched_fields.append(f"custom_{enricher.__name__}")
                except Exception as e:
                    result.errors.append(f"Custom enricher failed: {e}")

        except Exception as e:
            result.errors.append(f"Enrichment failed: {e}")

        result.enriched_fields = enriched_fields
        result.processing_time_ms = (time.time() - start_time) * 1000

        return result

    async def _fetch_service_metadata(self, service: str) -> ServiceMetadata | None:
        """Fetch metadata for a service.

        Args:
            service: Service name

        Returns:
            Service metadata or None if not found
        """
        # In a real implementation, this would query a service registry
        # like Consul, etcd, or a custom service catalog
        # For now, return basic metadata
        return ServiceMetadata(
            name=service,
            environment=settings.env,
        )

    async def _fetch_host_metadata(self, host: str) -> HostMetadata | None:
        """Fetch metadata for a host.

        Args:
            host: Host name or IP

        Returns:
            Host metadata or None if not found
        """
        # In a real implementation, this would query a CMDB or cloud API
        # For now, return basic metadata
        return HostMetadata(hostname=host)

    def _calculate_derived_metrics(self, metric: dict[str, Any]) -> dict[str, Any]:
        """Calculate derived metrics from base metric.

        Args:
            metric: Base metric data

        Returns:
            Dictionary of derived metrics
        """
        derived = {}

        value = metric.get("value")
        if value is not None:
            try:
                val = float(value)

                # Rate calculation (if previous value available)
                if "previous_value" in metric and "time_diff_seconds" in metric:
                    prev = float(metric["previous_value"])
                    time_diff = float(metric["time_diff_seconds"])
                    if time_diff > 0:
                        derived["rate"] = (val - prev) / time_diff

                # Percentage change
                if "previous_value" in metric:
                    prev = float(metric["previous_value"])
                    if prev != 0:
                        derived["percent_change"] = ((val - prev) / abs(prev)) * 100

                # Value categorization
                if val == 0:
                    derived["value_category"] = "zero"
                elif val > 0:
                    derived["value_category"] = "positive"
                else:
                    derived["value_category"] = "negative"

            except (ValueError, TypeError):
                pass

        return derived

    def _extract_log_patterns(self, message: str) -> dict[str, Any]:
        """Extract patterns from log message.

        Args:
            message: Log message

        Returns:
            Dictionary of extracted patterns
        """
        import re

        patterns = {}

        # Extract error codes
        error_patterns = [
            r"Error\s*[:\-]?\s*(\w+)",
            r"Exception\s*[:\-]?\s*(\w+)",
            r"ERR[_-]?(\w+)",
            r"code[:\s]*(\d+)",
        ]

        error_codes = []
        for pattern in error_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            error_codes.extend(matches)

        if error_codes:
            patterns["error_codes"] = error_codes

        # Extract IDs (UUIDs, trace IDs, etc.)
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        uuids = re.findall(uuid_pattern, message, re.IGNORECASE)
        if uuids:
            patterns["uuids"] = uuids

        # Extract IP addresses
        ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        ips = re.findall(ip_pattern, message)
        if ips:
            patterns["ip_addresses"] = ips

        # Extract durations
        duration_pattern = r"(\d+(?:\.\d+)?)\s*(ms|s|seconds?|minutes?|hours?)"
        durations = re.findall(duration_pattern, message, re.IGNORECASE)
        if durations:
            patterns["durations"] = [f"{val} {unit}" for val, unit in durations]

        # Extract file paths
        path_pattern = r"(?:[\w.-]+[/\\])+[\w.-]+\.\w+"
        paths = re.findall(path_pattern, message)
        if paths:
            patterns["file_paths"] = paths

        # Detect log level from message content
        if re.search(r"\b(error|exception|failed|failure)\b", message, re.IGNORECASE):
            patterns["detected_level"] = "ERROR"
        elif re.search(r"\b(warn|warning|caution)\b", message, re.IGNORECASE):
            patterns["detected_level"] = "WARNING"
        elif re.search(r"\b(debug|trace)\b", message, re.IGNORECASE):
            patterns["detected_level"] = "DEBUG"

        return patterns

    def _extract_correlation_info(self, event: dict[str, Any]) -> dict[str, Any]:
        """Extract correlation information from event.

        Args:
            event: Event data

        Returns:
            Dictionary of correlation information
        """
        correlation = {}
        metadata = event.get("metadata", {})

        # Extract trace IDs
        if "trace_id" in metadata:
            correlation["trace_id"] = metadata["trace_id"]

        # Extract span IDs
        if "span_id" in metadata:
            correlation["span_id"] = metadata["span_id"]

        # Extract parent event IDs
        if "parent_event_id" in metadata:
            correlation["parent_event_id"] = metadata["parent_event_id"]

        # Extract correlation IDs
        if "correlation_id" in metadata:
            correlation["correlation_id"] = metadata["correlation_id"]

        # Extract alert group
        if "group_key" in metadata:
            correlation["group_key"] = metadata["group_key"]

        return correlation

    def add_custom_enricher(
        self,
        enricher: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        """Add a custom enrichment function.

        Args:
            enricher: Function that takes and returns a dictionary
        """
        self.config.custom_enrichers.append(enricher)

    def clear_cache(self) -> None:
        """Clear the service and host metadata caches."""
        self._service_cache.clear()
        self._host_cache.clear()

    async def enrich_batch(
        self,
        items: list[dict[str, Any]],
        item_type: str = "metric",
    ) -> list[EnrichmentResult]:
        """Enrich a batch of items.

        Args:
            items: List of items to enrich
            item_type: Type of items ('metric', 'log', or 'event')

        Returns:
            List of enrichment results
        """
        results = []

        enrich_method = {
            "metric": self.enrich_metric,
            "log": self.enrich_log,
            "event": self.enrich_event,
        }.get(item_type, self.enrich_metric)

        for item in items:
            result = await enrich_method(item)
            results.append(result)

        return results

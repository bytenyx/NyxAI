"""Data normalization module for NyxAI.

This module provides data normalization capabilities for metrics, logs,
and events to ensure consistent data format for downstream processing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class Normalizable(Protocol):
    """Protocol for normalizable data objects."""

    def to_dict(self) -> dict[str, Any]:
        """Convert object to dictionary."""
        ...


@dataclass
class NormalizationConfig:
    """Configuration for data normalization.

    Attributes:
        remove_nulls: Whether to remove null values
        trim_strings: Whether to trim whitespace from strings
        lowercase_keys: Whether to convert dictionary keys to lowercase
        normalize_timestamps: Whether to normalize timestamps to UTC
        fill_missing_numeric: Value to use for missing numeric fields
        max_string_length: Maximum length for string values
        remove_duplicates: Whether to remove duplicate entries
        sort_keys: Whether to sort dictionary keys
    """

    remove_nulls: bool = True
    trim_strings: bool = True
    lowercase_keys: bool = False
    normalize_timestamps: bool = True
    fill_missing_numeric: float | None = None
    max_string_length: int | None = None
    remove_duplicates: bool = True
    sort_keys: bool = False


@dataclass
class NormalizationResult:
    """Result of data normalization.

    Attributes:
        data: Normalized data
        original_count: Original number of records
        normalized_count: Number of records after normalization
        removed_nulls: Number of null values removed
        removed_duplicates: Number of duplicates removed
        truncated_strings: Number of strings truncated
        errors: List of errors encountered during normalization
        processing_time_ms: Time taken to normalize in milliseconds
    """

    data: list[dict[str, Any]] = field(default_factory=list)
    original_count: int = 0
    normalized_count: int = 0
    removed_nulls: int = 0
    removed_duplicates: int = 0
    truncated_strings: int = 0
    errors: list[str] = field(default_factory=list)
    processing_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "data": self.data,
            "original_count": self.original_count,
            "normalized_count": self.normalized_count,
            "removed_nulls": self.removed_nulls,
            "removed_duplicates": self.removed_duplicates,
            "truncated_strings": self.truncated_strings,
            "errors": self.errors,
            "processing_time_ms": self.processing_time_ms,
        }


class NormalizedMetric(BaseModel):
    """Normalized metric data model.

    Attributes:
        name: Metric name
        value: Metric value
        timestamp: Metric timestamp
        labels: Metric labels/tags
        source: Data source
        unit: Metric unit
    """

    model_config = ConfigDict(extra="allow")

    name: str
    value: float
    timestamp: datetime
    labels: dict[str, str] = Field(default_factory=dict)
    source: str = "unknown"
    unit: str | None = None


class NormalizedLog(BaseModel):
    """Normalized log data model.

    Attributes:
        message: Log message
        timestamp: Log timestamp
        level: Log level
        service: Service name
        host: Host name
        source: Log source
        metadata: Additional metadata
    """

    model_config = ConfigDict(extra="allow")

    message: str
    timestamp: datetime
    level: str = "INFO"
    service: str | None = None
    host: str | None = None
    source: str = "unknown"
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedEvent(BaseModel):
    """Normalized event data model.

    Attributes:
        event_type: Type of event
        title: Event title
        description: Event description
        timestamp: Event timestamp
        severity: Event severity
        source: Event source
        service: Service name
        host: Host name
        metadata: Additional metadata
    """

    model_config = ConfigDict(extra="allow")

    event_type: str
    title: str
    description: str | None = None
    timestamp: datetime
    severity: str = "info"
    source: str = "unknown"
    service: str | None = None
    host: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DataNormalizer:
    """Data normalizer for NyxAI collectors.

    This class provides methods to normalize various data types
    (metrics, logs, events) into a consistent format.

    Example:
        >>> normalizer = DataNormalizer()
        >>> # Normalize metrics
        >>> result = normalizer.normalize_metrics(raw_metrics)
        >>> # Normalize logs
        >>> result = normalizer.normalize_logs(raw_logs)
    """

    def __init__(self, config: NormalizationConfig | None = None) -> None:
        """Initialize the data normalizer.

        Args:
            config: Normalization configuration
        """
        self.config = config or NormalizationConfig()

    def normalize_metrics(
        self,
        metrics: list[dict[str, Any]],
        source: str = "prometheus",
    ) -> NormalizationResult:
        """Normalize metric data.

        Args:
            metrics: List of raw metric dictionaries
            source: Data source identifier

        Returns:
            Normalization result with normalized metrics
        """
        import time

        start_time = time.time()
        result = NormalizationResult(original_count=len(metrics))

        seen_keys: set[str] = set()

        for metric in metrics:
            try:
                normalized = self._normalize_single_metric(metric, source)

                if normalized is None:
                    result.removed_nulls += 1
                    continue

                # Check for duplicates
                if self.config.remove_duplicates:
                    key = self._get_metric_key(normalized)
                    if key in seen_keys:
                        result.removed_duplicates += 1
                        continue
                    seen_keys.add(key)

                result.data.append(normalized)

            except Exception as e:
                result.errors.append(f"Failed to normalize metric: {e}")

        result.normalized_count = len(result.data)
        result.processing_time_ms = (time.time() - start_time) * 1000

        return result

    def _normalize_single_metric(
        self,
        metric: dict[str, Any],
        source: str,
    ) -> dict[str, Any] | None:
        """Normalize a single metric.

        Args:
            metric: Raw metric dictionary
            source: Data source

        Returns:
            Normalized metric dictionary or None if invalid
        """
        # Extract metric name and labels
        metric_name = metric.get("__name__", metric.get("name", "unknown"))
        labels = {k: v for k, v in metric.items() if not k.startswith("_") and k != "value"}

        # Extract value
        value = metric.get("value")
        if value is None and "values" in metric:
            # Handle range query results - take the latest value
            values = metric["values"]
            if values:
                value = values[-1][1] if isinstance(values[-1], (list, tuple)) else values[-1]

        if value is None and self.config.remove_nulls:
            return None

        # Convert value to float
        try:
            value = float(value) if value is not None else self.config.fill_missing_numeric
        except (ValueError, TypeError):
            if self.config.remove_nulls:
                return None
            value = self.config.fill_missing_numeric

        # Extract timestamp
        timestamp = metric.get("timestamp")
        if timestamp is None:
            timestamp = datetime.utcnow()
        elif isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)

        # Normalize timestamp
        if self.config.normalize_timestamps and isinstance(timestamp, datetime):
            timestamp = timestamp.replace(tzinfo=None)

        normalized = {
            "name": self._normalize_string(metric_name),
            "value": value,
            "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            "labels": self._normalize_dict(labels),
            "source": source,
            "unit": metric.get("unit"),
        }

        return self._apply_common_transforms(normalized)

    def normalize_logs(
        self,
        logs: list[dict[str, Any]],
        source: str = "loki",
    ) -> NormalizationResult:
        """Normalize log data.

        Args:
            logs: List of raw log dictionaries
            source: Data source identifier

        Returns:
            Normalization result with normalized logs
        """
        import time

        start_time = time.time()
        result = NormalizationResult(original_count=len(logs))

        seen_messages: set[str] = set()

        for log in logs:
            try:
                normalized = self._normalize_single_log(log, source)

                if normalized is None:
                    result.removed_nulls += 1
                    continue

                # Check for duplicates
                if self.config.remove_duplicates:
                    key = f"{normalized.get('timestamp')}_{normalized.get('message', '')}"
                    if key in seen_messages:
                        result.removed_duplicates += 1
                        continue
                    seen_messages.add(key)

                result.data.append(normalized)

            except Exception as e:
                result.errors.append(f"Failed to normalize log: {e}")

        result.normalized_count = len(result.data)
        result.processing_time_ms = (time.time() - start_time) * 1000

        return result

    def _normalize_single_log(
        self,
        log: dict[str, Any],
        source: str,
    ) -> dict[str, Any] | None:
        """Normalize a single log entry.

        Args:
            log: Raw log dictionary
            source: Data source

        Returns:
            Normalized log dictionary or None if invalid
        """
        # Extract message
        message = log.get("message", log.get("msg", log.get("log", "")))
        if not message and self.config.remove_nulls:
            return None

        message = self._normalize_string(str(message))

        # Truncate if necessary
        if self.config.max_string_length and len(message) > self.config.max_string_length:
            message = message[: self.config.max_string_length]

        # Extract timestamp
        timestamp = log.get("timestamp", log.get("ts", log.get("time")))
        if timestamp is None:
            timestamp = datetime.utcnow()
        elif isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.utcnow()

        # Normalize timestamp
        if self.config.normalize_timestamps and isinstance(timestamp, datetime):
            timestamp = timestamp.replace(tzinfo=None)

        # Extract level
        level = log.get("level", log.get("severity", "INFO")).upper()
        valid_levels = {"DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL", "FATAL"}
        if level not in valid_levels:
            level = "INFO"
        if level == "WARN":
            level = "WARNING"
        if level == "FATAL":
            level = "CRITICAL"

        # Extract metadata (everything else)
        metadata = {
            k: v
            for k, v in log.items()
            if k not in {"message", "msg", "log", "timestamp", "ts", "time", "level", "severity"}
        }

        normalized = {
            "message": message,
            "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            "level": level,
            "service": log.get("service") or log.get("app"),
            "host": log.get("host") or log.get("hostname") or log.get("instance"),
            "source": source,
            "metadata": self._normalize_dict(metadata),
        }

        return self._apply_common_transforms(normalized)

    def normalize_events(
        self,
        events: list[dict[str, Any]],
        source: str = "system",
    ) -> NormalizationResult:
        """Normalize event data.

        Args:
            events: List of raw event dictionaries
            source: Data source identifier

        Returns:
            Normalization result with normalized events
        """
        import time

        start_time = time.time()
        result = NormalizationResult(original_count=len(events))

        seen_events: set[str] = set()

        for event in events:
            try:
                normalized = self._normalize_single_event(event, source)

                if normalized is None:
                    result.removed_nulls += 1
                    continue

                # Check for duplicates
                if self.config.remove_duplicates:
                    key = f"{normalized.get('timestamp')}_{normalized.get('title', '')}"
                    if key in seen_events:
                        result.removed_duplicates += 1
                        continue
                    seen_events.add(key)

                result.data.append(normalized)

            except Exception as e:
                result.errors.append(f"Failed to normalize event: {e}")

        result.normalized_count = len(result.data)
        result.processing_time_ms = (time.time() - start_time) * 1000

        return result

    def _normalize_single_event(
        self,
        event: dict[str, Any],
        source: str,
    ) -> dict[str, Any] | None:
        """Normalize a single event.

        Args:
            event: Raw event dictionary
            source: Data source

        Returns:
            Normalized event dictionary or None if invalid
        """
        # Extract required fields
        event_type = event.get("event_type", event.get("type", "custom"))
        title = event.get("title", event.get("name", event.get("alertname")))

        if not title and self.config.remove_nulls:
            return None

        title = self._normalize_string(str(title))

        # Truncate if necessary
        if self.config.max_string_length and len(title) > self.config.max_string_length:
            title = title[: self.config.max_string_length]

        # Extract timestamp
        timestamp = event.get("timestamp", event.get("startsAt", event.get("created_at")))
        if timestamp is None:
            timestamp = datetime.utcnow()
        elif isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.utcnow()

        # Normalize timestamp
        if self.config.normalize_timestamps and isinstance(timestamp, datetime):
            timestamp = timestamp.replace(tzinfo=None)

        # Extract severity
        severity = event.get("severity", event.get("priority", "info")).lower()
        valid_severities = {"critical", "high", "medium", "low", "info", "warning"}
        if severity not in valid_severities:
            severity = "info"
        if severity == "warning":
            severity = "medium"

        # Extract metadata
        metadata = {
            k: v
            for k, v in event.items()
            if k
            not in {
                "event_type",
                "type",
                "title",
                "name",
                "alertname",
                "timestamp",
                "startsAt",
                "created_at",
                "severity",
                "priority",
                "description",
                "message",
                "source",
                "service",
                "host",
            }
        }

        normalized = {
            "event_type": event_type.lower(),
            "title": title,
            "description": event.get("description", event.get("message")),
            "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            "severity": severity,
            "source": source,
            "service": event.get("service") or event.get("job"),
            "host": event.get("host") or event.get("instance", "").split(":")[0],
            "metadata": self._normalize_dict(metadata),
        }

        return self._apply_common_transforms(normalized)

    def _normalize_string(self, value: str) -> str:
        """Normalize a string value.

        Args:
            value: String to normalize

        Returns:
            Normalized string
        """
        if self.config.trim_strings:
            value = value.strip()
        return value

    def _normalize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize a dictionary.

        Args:
            data: Dictionary to normalize

        Returns:
            Normalized dictionary
        """
        result = {}
        for key, value in data.items():
            # Normalize key
            if self.config.lowercase_keys:
                key = key.lower()

            # Normalize value
            if isinstance(value, str):
                value = self._normalize_string(value)
                if self.config.max_string_length and len(value) > self.config.max_string_length:
                    value = value[: self.config.max_string_length]
            elif isinstance(value, dict):
                value = self._normalize_dict(value)
            elif isinstance(value, list):
                value = self._normalize_list(value)
            elif isinstance(value, datetime):
                if self.config.normalize_timestamps:
                    value = value.replace(tzinfo=None)
                value = value.isoformat()

            # Skip nulls if configured
            if value is None and self.config.remove_nulls:
                continue

            result[key] = value

        if self.config.sort_keys:
            result = dict(sorted(result.items()))

        return result

    def _normalize_list(self, data: list[Any]) -> list[Any]:
        """Normalize a list.

        Args:
            data: List to normalize

        Returns:
            Normalized list
        """
        result = []
        for item in data:
            if isinstance(item, str):
                item = self._normalize_string(item)
            elif isinstance(item, dict):
                item = self._normalize_dict(item)
            elif isinstance(item, list):
                item = self._normalize_list(item)

            if item is not None or not self.config.remove_nulls:
                result.append(item)

        return result

    def _apply_common_transforms(self, data: dict[str, Any]) -> dict[str, Any]:
        """Apply common transformations to normalized data.

        Args:
            data: Data to transform

        Returns:
            Transformed data
        """
        if self.config.sort_keys:
            data = dict(sorted(data.items()))
        return data

    def _get_metric_key(self, metric: dict[str, Any]) -> str:
        """Generate a unique key for a metric.

        Args:
            metric: Normalized metric

        Returns:
            Unique key string
        """
        labels_str = "_".join(f"{k}={v}" for k, v in sorted(metric.get("labels", {}).items()))
        return f"{metric.get('name', '')}_{labels_str}_{metric.get('timestamp', '')}"

    def normalize_time_series(
        self,
        timestamps: list[datetime],
        values: list[float],
        fill_gaps: bool = False,
        interval_seconds: int = 60,
    ) -> tuple[list[datetime], list[float]]:
        """Normalize time series data.

        Args:
            timestamps: List of timestamps
            values: List of values
            fill_gaps: Whether to fill gaps in the time series
            interval_seconds: Expected interval between data points

        Returns:
            Tuple of (normalized_timestamps, normalized_values)
        """
        if len(timestamps) != len(values):
            raise ValueError("Timestamps and values must have the same length")

        if not timestamps:
            return [], []

        # Sort by timestamp
        sorted_pairs = sorted(
            zip(timestamps, values, strict=False), key=lambda x: x[0]
        )
        sorted_timestamps = [p[0] for p in sorted_pairs]
        sorted_values = [p[1] for p in sorted_pairs]

        if not fill_gaps:
            return sorted_timestamps, sorted_values

        # Fill gaps with interpolated values
        filled_timestamps = []
        filled_values = []

        current_time = sorted_timestamps[0]
        end_time = sorted_timestamps[-1]
        value_idx = 0

        while current_time <= end_time:
            filled_timestamps.append(current_time)

            # Find the closest value
            while (
                value_idx < len(sorted_timestamps) - 1
                and sorted_timestamps[value_idx + 1] <= current_time
            ):
                value_idx += 1

            if value_idx < len(sorted_values):
                filled_values.append(sorted_values[value_idx])
            else:
                filled_values.append(sorted_values[-1] if sorted_values else 0.0)

            current_time = datetime.fromtimestamp(
                current_time.timestamp() + interval_seconds
            )

        return filled_timestamps, filled_values

    def remove_outliers(
        self,
        values: list[float],
        method: str = "iqr",
        threshold: float = 1.5,
    ) -> list[float | None]:
        """Remove outliers from a list of values.

        Args:
            values: List of numeric values
            method: Outlier detection method ('iqr' or 'zscore')
            threshold: Threshold for outlier detection

        Returns:
            List of values with outliers replaced by None
        """
        if not values:
            return []

        if method == "iqr":
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            return [v if lower_bound <= v <= upper_bound else None for v in values]

        elif method == "zscore":
            mean = np.mean(values)
            std = np.std(values)
            if std == 0:
                return values

            return [v if abs((v - mean) / std) <= threshold else None for v in values]

        else:
            raise ValueError(f"Unknown outlier detection method: {method}")

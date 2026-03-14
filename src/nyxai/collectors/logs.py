"""Loki log collector for NyxAI.

This module provides asynchronous collection of logs from Grafana Loki
using LogQL queries via HTTP API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urljoin

import httpx


@dataclass
class LokiStream:
    """A single log stream from Loki.

    Attributes:
        labels: Dictionary of stream labels
        values: List of (timestamp, log_line) tuples
    """

    labels: dict[str, str] = field(default_factory=dict)
    values: list[tuple[datetime, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert stream to dictionary format."""
        return {
            "labels": self.labels,
            "values": [
                {"timestamp": ts.isoformat(), "message": msg}
                for ts, msg in self.values
            ],
        }


@dataclass
class LokiQueryResult:
    """Result of a Loki query.

    Attributes:
        streams: List of log streams
        query: The original query string
        query_time: When the query was executed
        result_type: Type of result (streams or matrix)
        stats: Query statistics from Loki
    """

    streams: list[LokiStream] = field(default_factory=list)
    query: str = ""
    query_time: datetime | None = None
    result_type: str = ""
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def total_lines(self) -> int:
        """Get total number of log lines across all streams."""
        return sum(len(stream.values) for stream in self.streams)

    def get_all_messages(self) -> list[str]:
        """Get all log messages as a flat list."""
        messages = []
        for stream in self.streams:
            messages.extend(msg for _, msg in stream.values)
        return messages

    def filter_by_label(self, label: str, value: str) -> list[LokiStream]:
        """Filter streams by a specific label value.

        Args:
            label: Label name to filter by
            value: Label value to match

        Returns:
            List of matching streams
        """
        return [
            stream for stream in self.streams if stream.labels.get(label) == value
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "streams": [stream.to_dict() for stream in self.streams],
            "query": self.query,
            "query_time": self.query_time.isoformat() if self.query_time else None,
            "result_type": self.result_type,
            "stats": self.stats,
            "total_lines": self.total_lines,
        }


class LokiCollector:
    """Asynchronous collector for Grafana Loki logs.

    This collector supports LogQL queries for log aggregation and filtering.
    It uses httpx for async HTTP requests.

    Example:
        >>> collector = LokiCollector("http://localhost:3100")
        >>> # Simple log query
        >>> result = await collector.query(
        ...     '{job="varlogs"} |= "error"',
        ...     limit=100
        ... )
        >>> # Range query with time bounds
        >>> result = await collector.query_range(
        ...     'rate({job="varlogs"} |= "error" [5m])',
        ...     start=datetime.now() - timedelta(hours=1),
        ...     end=datetime.now(),
        ...     step=300
        ... )
    """

    def __init__(
        self,
        url: str | None = None,
        timeout: int = 30,
        headers: dict[str, str] | None = None,
        org_id: str | None = None,
    ) -> None:
        """Initialize the Loki collector.

        Args:
            url: Loki server URL. Defaults to http://localhost:3100
            timeout: Request timeout in seconds
            headers: Additional HTTP headers to include in requests
            org_id: Optional X-Scope-OrgID for multi-tenant Loki
        """
        self.url = (url or "http://localhost:3100").rstrip("/")
        self.timeout = timeout
        self.headers = headers or {}
        self.org_id = org_id

        if org_id:
            self.headers["X-Scope-OrgID"] = org_id

    def _prepare_timestamp(self, dt: datetime) -> int:
        """Convert datetime to nanoseconds timestamp for Loki.

        Args:
            dt: Datetime to convert

        Returns:
            Timestamp in nanoseconds
        """
        return int(dt.timestamp() * 1e9)

    def _parse_timestamp(self, ts: str) -> datetime:
        """Parse Loki timestamp to datetime.

        Args:
            ts: Timestamp string in nanoseconds

        Returns:
            Parsed datetime
        """
        return datetime.fromtimestamp(int(ts) / 1e9)

    async def query(
        self,
        query: str,
        limit: int = 100,
        time: datetime | None = None,
        direction: str = "backward",
    ) -> LokiQueryResult:
        """Execute a LogQL query.

        Args:
            query: LogQL query string
            limit: Maximum number of entries to return
            time: Optional end time for the query (defaults to now)
            direction: Query direction ('forward' or 'backward')

        Returns:
            Query result containing log streams

        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response format is unexpected
        """
        params: dict[str, Any] = {
            "query": query,
            "limit": limit,
            "direction": direction,
        }

        if time:
            params["time"] = self._prepare_timestamp(time)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                urljoin(self.url, "/loki/api/v1/query"),
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_query_response(data, query)

    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        limit: int = 100,
        step: int | None = None,
        direction: str = "backward",
    ) -> LokiQueryResult:
        """Execute a LogQL range query.

        Args:
            query: LogQL query string
            start: Start time for the range
            end: End time for the range
            limit: Maximum number of entries to return per stream
            step: Query resolution step width in seconds
            direction: Query direction ('forward' or 'backward')

        Returns:
            Query result containing log streams

        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response format is unexpected
        """
        params: dict[str, Any] = {
            "query": query,
            "start": self._prepare_timestamp(start),
            "end": self._prepare_timestamp(end),
            "limit": limit,
            "direction": direction,
        }

        if step:
            params["step"] = step

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                urljoin(self.url, "/loki/api/v1/query_range"),
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_query_response(data, query)

    def _parse_query_response(
        self,
        data: dict[str, Any],
        query: str,
    ) -> LokiQueryResult:
        """Parse Loki query response.

        Args:
            data: Response data from Loki
            query: Original query string

        Returns:
            Parsed query result

        Raises:
            ValueError: If the response format is unexpected
        """
        if data.get("status") != "success":
            error_msg = data.get("error", "Unknown error")
            raise ValueError(f"Loki query failed: {error_msg}")

        result_data = data.get("data", {})
        result_type = result_data.get("resultType", "")
        results = result_data.get("result", [])
        stats = data.get("statistics", {})

        streams: list[LokiStream] = []

        if result_type == "streams":
            for item in results:
                stream_labels = item.get("stream", {})
                values = item.get("values", [])
                parsed_values = [
                    (self._parse_timestamp(ts), msg) for ts, msg in values
                ]
                streams.append(
                    LokiStream(labels=stream_labels, values=parsed_values)
                )
        elif result_type == "matrix":
            # Metric query results (for aggregations)
            for item in results:
                metric = item.get("metric", {})
                values = item.get("values", [])
                # Convert metric values to log-like format
                parsed_values = [
                    (self._parse_timestamp(ts), str(val)) for ts, val in values
                ]
                streams.append(LokiStream(labels=metric, values=parsed_values))

        return LokiQueryResult(
            streams=streams,
            query=query,
            query_time=datetime.now(),
            result_type=result_type,
            stats=stats,
        )

    async def label_names(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[str]:
        """Get all label names.

        Args:
            start: Optional start time
            end: Optional end time

        Returns:
            List of label names

        Raises:
            httpx.HTTPError: If the request fails
        """
        params: dict[str, Any] = {}
        if start:
            params["start"] = self._prepare_timestamp(start)
        if end:
            params["end"] = self._prepare_timestamp(end)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                urljoin(self.url, "/loki/api/v1/label"),
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "success":
            error_msg = data.get("error", "Unknown error")
            raise ValueError(f"Failed to get label names: {error_msg}")

        return data.get("data", [])

    async def label_values(
        self,
        label: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[str]:
        """Get all values for a specific label.

        Args:
            label: Label name to query
            start: Optional start time
            end: Optional end time

        Returns:
            List of label values

        Raises:
            httpx.HTTPError: If the request fails
        """
        params: dict[str, Any] = {}
        if start:
            params["start"] = self._prepare_timestamp(start)
        if end:
            params["end"] = self._prepare_timestamp(end)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                urljoin(self.url, f"/loki/api/v1/label/{label}/values"),
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "success":
            error_msg = data.get("error", "Unknown error")
            raise ValueError(f"Failed to get label values: {error_msg}")

        return data.get("data", [])

    async def series(
        self,
        match: list[str],
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[dict[str, str]]:
        """Get series that match the given selectors.

        Args:
            match: List of log stream selectors
            start: Optional start time
            end: Optional end time

        Returns:
            List of series labels

        Raises:
            httpx.HTTPError: If the request fails
        """
        params: dict[str, Any] = {"match[]": match}
        if start:
            params["start"] = self._prepare_timestamp(start)
        if end:
            params["end"] = self._prepare_timestamp(end)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                urljoin(self.url, "/loki/api/v1/series"),
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "success":
            error_msg = data.get("error", "Unknown error")
            raise ValueError(f"Failed to get series: {error_msg}")

        return data.get("data", [])

    async def health_check(self) -> bool:
        """Check if Loki server is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    urljoin(self.url, "/ready"),
                    headers=self.headers,
                )
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def get_logs_by_service(
        self,
        service: str,
        duration: timedelta = timedelta(hours=1),
        level: str | None = None,
        limit: int = 100,
    ) -> LokiQueryResult:
        """Get logs for a specific service.

        This is a convenience method for common service log queries.

        Args:
            service: Service name
            duration: Time range to query
            level: Optional log level filter (e.g., 'error', 'warn')
            limit: Maximum number of entries

        Returns:
            Query result containing log streams
        """
        end = datetime.now()
        start = end - duration

        # Build query
        query_parts = [f'{{service="{service}"}}']
        if level:
            query_parts.append(f'|="{level}"')

        query = " ".join(query_parts)

        return await self.query_range(
            query=query,
            start=start,
            end=end,
            limit=limit,
        )

    async def get_error_logs(
        self,
        duration: timedelta = timedelta(hours=1),
        limit: int = 100,
    ) -> LokiQueryResult:
        """Get error logs across all services.

        This is a convenience method for fetching error logs.

        Args:
            duration: Time range to query
            limit: Maximum number of entries

        Returns:
            Query result containing error log streams
        """
        end = datetime.now()
        start = end - duration

        # Common error level patterns
        query = '{job=~".+", level=~"(?i)(error|fatal|critical)"}'

        return await self.query_range(
            query=query,
            start=start,
            end=end,
            limit=limit,
        )

    async def tail(
        self,
        query: str,
        delay_for: int = 0,
        limit: int = 100,
    ) -> LokiQueryResult:
        """Tail logs in real-time (WebSocket alternative using polling).

        Note: This uses the HTTP tail endpoint which returns immediately.
        For true streaming, use WebSocket directly.

        Args:
            query: LogQL query string
            delay_for: Delay in seconds to ensure logs are ingested
            limit: Maximum number of entries

        Returns:
            Query result containing new log streams

        Raises:
            httpx.HTTPError: If the request fails
        """
        params: dict[str, Any] = {
            "query": query,
            "limit": limit,
        }

        if delay_for:
            params["delay_for"] = delay_for

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                urljoin(self.url, "/loki/api/v1/tail"),
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_query_response(data, query)

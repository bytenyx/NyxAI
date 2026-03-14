"""Prometheus metrics collector for NyxAI.

This module provides asynchronous collection of metrics from Prometheus
using both instant and range queries with PromQL support.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx
from prometheus_api_client import PrometheusConnect

from nyxai.config import settings


@dataclass
class PrometheusQueryResult:
    """Result of a Prometheus query.

    Attributes:
        metric: Dictionary of metric labels
        values: List of (timestamp, value) tuples for range queries
        value: Single (timestamp, value) tuple for instant queries
        query: The original query string
        query_time: When the query was executed
    """

    metric: dict[str, str]
    values: list[tuple[datetime, float]] | None = None
    value: tuple[datetime, float] | None = None
    query: str = ""
    query_time: datetime | None = None

    @property
    def is_range_query(self) -> bool:
        """Check if this result is from a range query."""
        return self.values is not None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary format."""
        result: dict[str, Any] = {
            "metric": self.metric,
            "query": self.query,
            "query_time": self.query_time.isoformat() if self.query_time else None,
        }
        if self.is_range_query:
            result["values"] = [
                {"timestamp": ts.isoformat(), "value": val}
                for ts, val in self.values or []
            ]
        else:
            result["value"] = (
                {
                    "timestamp": self.value[0].isoformat(),
                    "value": self.value[1],
                }
                if self.value
                else None
            )
        return result


class PrometheusCollector:
    """Asynchronous collector for Prometheus metrics.

    This collector supports both instant and range queries using PromQL.
    It uses httpx for async HTTP requests and prometheus-api-client for
    additional functionality.

    Example:
        >>> collector = PrometheusCollector()
        >>> # Instant query
        >>> result = await collector.query('up{job="prometheus"}')
        >>> # Range query
        >>> results = await collector.query_range(
        ...     'rate(http_requests_total[5m])',
        ...     start=datetime.now() - timedelta(hours=1),
        ...     end=datetime.now(),
        ...     step='1m'
        ... )
    """

    def __init__(
        self,
        url: str | None = None,
        timeout: int | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize the Prometheus collector.

        Args:
            url: Prometheus server URL. Defaults to settings.prometheus.url
            timeout: Request timeout in seconds. Defaults to settings.prometheus.timeout
            headers: Additional HTTP headers to include in requests
        """
        self.url = url or settings.prometheus.url
        self.timeout = timeout or settings.prometheus.timeout
        self.headers = headers or {}

        # Ensure URL doesn't end with trailing slash for consistency
        self.url = self.url.rstrip("/")

        # Initialize sync client for some operations
        self._sync_client: PrometheusConnect | None = None

    def _get_sync_client(self) -> PrometheusConnect:
        """Get or create synchronous Prometheus client."""
        if self._sync_client is None:
            self._sync_client = PrometheusConnect(
                url=self.url,
                headers=self.headers,
                disable_ssl=True,
            )
        return self._sync_client

    async def query(
        self,
        query: str,
        time: datetime | None = None,
        timeout: int | None = None,
    ) -> list[PrometheusQueryResult]:
        """Execute an instant PromQL query.

        Args:
            query: PromQL query string
            time: Optional specific time to query (defaults to now)
            timeout: Optional query timeout override

        Returns:
            List of query results

        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response format is unexpected
        """
        params: dict[str, str] = {"query": query}
        if time:
            params["time"] = time.isoformat()

        async with httpx.AsyncClient(timeout=timeout or self.timeout) as client:
            response = await client.get(
                f"{self.url}/api/v1/query",
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "success":
            error_msg = data.get("error", "Unknown error")
            raise ValueError(f"Prometheus query failed: {error_msg}")

        result_data = data.get("data", {}).get("result", [])
        query_time = datetime.now()

        return [
            PrometheusQueryResult(
                metric=item.get("metric", {}),
                value=(
                    (datetime.fromtimestamp(item["value"][0]), float(item["value"][1]))
                    if "value" in item
                    else None
                ),
                query=query,
                query_time=query_time,
            )
            for item in result_data
        ]

    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str | None = None,
        timeout: int | None = None,
    ) -> list[PrometheusQueryResult]:
        """Execute a range PromQL query.

        Args:
            query: PromQL query string
            start: Start time for the range
            end: End time for the range
            step: Query resolution step width (e.g., '1m', '15s')
            timeout: Optional query timeout override

        Returns:
            List of query results with time series data

        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response format is unexpected
        """
        step = step or settings.prometheus.step

        params: dict[str, str] = {
            "query": query,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "step": step,
        }

        async with httpx.AsyncClient(timeout=timeout or self.timeout) as client:
            response = await client.get(
                f"{self.url}/api/v1/query_range",
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "success":
            error_msg = data.get("error", "Unknown error")
            raise ValueError(f"Prometheus range query failed: {error_msg}")

        result_data = data.get("data", {}).get("result", [])
        query_time = datetime.now()

        results = []
        for item in result_data:
            values = item.get("values", [])
            parsed_values = [
                (datetime.fromtimestamp(ts), float(val)) for ts, val in values
            ]
            results.append(
                PrometheusQueryResult(
                    metric=item.get("metric", {}),
                    values=parsed_values,
                    query=query,
                    query_time=query_time,
                )
            )

        return results

    async def get_label_values(self, label: str) -> list[str]:
        """Get all values for a specific label.

        Args:
            label: Label name to query

        Returns:
            List of label values

        Raises:
            httpx.HTTPError: If the request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.url}/api/v1/label/{label}/values",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "success":
            error_msg = data.get("error", "Unknown error")
            raise ValueError(f"Failed to get label values: {error_msg}")

        return data.get("data", [])

    async def get_series(
        self,
        match: list[str],
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[dict[str, str]]:
        """Get time series that match the given label selectors.

        Args:
            match: List of series selectors
            start: Optional start time
            end: Optional end time

        Returns:
            List of series metadata

        Raises:
            httpx.HTTPError: If the request fails
        """
        params: dict[str, Any] = {"match[]": match}
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.url}/api/v1/series",
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
        """Check if Prometheus server is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.url}/-/healthy",
                    headers=self.headers,
                )
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def get_metrics_list(self) -> list[str]:
        """Get list of available metric names.

        Returns:
            List of metric names

        Raises:
            httpx.HTTPError: If the request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.url}/api/v1/label/__name__/values",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "success":
            error_msg = data.get("error", "Unknown error")
            raise ValueError(f"Failed to get metrics list: {error_msg}")

        return data.get("data", [])

    async def get_metric_metadata(
        self,
        metric: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Get metadata about metrics.

        Args:
            metric: Optional specific metric name
            limit: Maximum number of metrics to return

        Returns:
            Dictionary of metric metadata

        Raises:
            httpx.HTTPError: If the request fails
        """
        params: dict[str, Any] = {}
        if metric:
            params["metric"] = metric
        if limit:
            params["limit"] = limit

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.url}/api/v1/metadata",
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "success":
            error_msg = data.get("error", "Unknown error")
            raise ValueError(f"Failed to get metric metadata: {error_msg}")

        return data.get("data", {})

    async def get_common_metrics(
        self,
        duration: timedelta = timedelta(hours=1),
    ) -> dict[str, list[PrometheusQueryResult]]:
        """Get common system metrics for AIOps analysis.

        This is a convenience method that fetches commonly used metrics
        for anomaly detection and root cause analysis.

        Args:
            duration: Time range to fetch metrics for

        Returns:
            Dictionary mapping metric names to their query results
        """
        end = datetime.now()
        start = end - duration

        common_queries = {
            "cpu_usage": (
                '100 - (avg by (instance) '
                '(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
            ),
            "memory_usage": (
                '(1 - (node_memory_MemAvailable_bytes / '
                'node_memory_MemTotal_bytes)) * 100'
            ),
            "disk_usage": (
                '(1 - (node_filesystem_avail_bytes / '
                'node_filesystem_size_bytes)) * 100'
            ),
            "network_receive": "rate(node_network_receive_bytes_total[5m])",
            "network_transmit": "rate(node_network_transmit_bytes_total[5m])",
        }

        results = {}
        for name, query in common_queries.items():
            try:
                results[name] = await self.query_range(
                    query=query,
                    start=start,
                    end=end,
                    step="1m",
                )
            except (httpx.HTTPError, ValueError):
                # Skip metrics that fail to query
                results[name] = []

        return results

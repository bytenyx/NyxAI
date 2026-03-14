"""Prometheus query client for metrics retrieval.

This module provides an async interface to query Prometheus metrics,
including support for instant queries, range queries, and metadata retrieval.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx
from prometheus_api_client import PrometheusConnect

from nyxai.config import get_settings


@dataclass
class MetricValue:
    """Represents a single metric value with timestamp.

    Attributes:
        timestamp: The timestamp of the metric value.
        value: The metric value.
        labels: The labels associated with this metric.
    """

    timestamp: datetime
    value: float
    labels: dict[str, str]


@dataclass
class QueryResult:
    """Result of a Prometheus query.

    Attributes:
        metric_name: The name of the metric.
        labels: Common labels for all values.
        values: List of metric values (for range queries).
        value: Single metric value (for instant queries).
    """

    metric_name: str
    labels: dict[str, str]
    values: list[MetricValue] | None = None
    value: MetricValue | None = None


class PrometheusClient:
    """Async client for querying Prometheus metrics.

    This client wraps the prometheus-api-client library and provides
    async methods for querying metrics data.

    Example:
        >>> client = PrometheusClient()
        >>> result = await client.query("up")
        >>> range_data = await client.query_range(
        ...     "cpu_usage",
        ...     start=datetime.now() - timedelta(hours=1),
        ...     end=datetime.now(),
        ...     step="1m"
        ... )
    """

    def __init__(self, url: str | None = None, timeout: int = 30) -> None:
        """Initialize the Prometheus client.

        Args:
            url: Prometheus server URL. If None, uses settings.
            timeout: Request timeout in seconds.
        """
        settings = get_settings()
        self._url = url or settings.prometheus.url
        self._timeout = timeout or settings.prometheus.timeout
        self._client: PrometheusConnect | None = None
        self._async_client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        """Initialize the Prometheus connections."""
        if self._client is None:
            self._client = PrometheusConnect(
                url=self._url,
                disable_ssl=True,
            )
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self._url,
                timeout=self._timeout,
            )

    async def close(self) -> None:
        """Close the async HTTP client."""
        if self._async_client is not None:
            await self._async_client.aclose()
            self._async_client = None

    @property
    def client(self) -> PrometheusConnect:
        """Get the Prometheus client.

        Raises:
            RuntimeError: If the client has not been connected.

        Returns:
            PrometheusConnect: The Prometheus API client.
        """
        if self._client is None:
            raise RuntimeError("Prometheus client not connected. Call connect() first.")
        return self._client

    async def query(self, query: str, time: datetime | None = None) -> list[QueryResult]:
        """Execute an instant query.

        Args:
            query: The PromQL query string.
            time: Optional timestamp for the query. If None, uses current time.

        Returns:
            list[QueryResult]: List of query results.
        """
        params: dict[str, Any] = {"query": query}
        if time is not None:
            params["time"] = time.timestamp()

        response = await self._async_request("GET", "/api/v1/query", params=params)
        return self._parse_query_response(response)

    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "15s",
    ) -> list[QueryResult]:
        """Execute a range query.

        Args:
            query: The PromQL query string.
            start: Start time for the query range.
            end: End time for the query range.
            step: Query resolution step width (e.g., "1m", "5m", "1h").

        Returns:
            list[QueryResult]: List of query results with time series data.
        """
        params = {
            "query": query,
            "start": start.timestamp(),
            "end": end.timestamp(),
            "step": step,
        }

        response = await self._async_request("GET", "/api/v1/query_range", params=params)
        return self._parse_query_response(response)

    async def get_label_values(self, label: str) -> list[str]:
        """Get all values for a label.

        Args:
            label: The label name.

        Returns:
            list[str]: List of label values.
        """
        response = await self._async_request("GET", f"/api/v1/label/{label}/values")
        return response.get("data", [])

    async def get_series(
        self,
        match: list[str] | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[dict[str, str]]:
        """Get time series that match the given label selectors.

        Args:
            match: List of series selectors.
            start: Optional start time.
            end: Optional end time.

        Returns:
            list[dict[str, str]]: List of series metadata.
        """
        params: dict[str, Any] = {}
        if match:
            params["match[]"] = match
        if start:
            params["start"] = start.timestamp()
        if end:
            params["end"] = end.timestamp()

        response = await self._async_request("GET", "/api/v1/series", params=params)
        return response.get("data", [])

    async def get_metric_metadata(self, metric: str | None = None) -> dict[str, Any]:
        """Get metadata about metrics.

        Args:
            metric: Optional metric name to filter by.

        Returns:
            dict[str, Any]: Metric metadata.
        """
        params: dict[str, str] = {}
        if metric:
            params["metric"] = metric

        response = await self._async_request("GET", "/api/v1/metadata", params=params)
        return response.get("data", {})

    async def get_targets(self) -> dict[str, Any]:
        """Get information about current scrape targets.

        Returns:
            dict[str, Any]: Target information.
        """
        response = await self._async_request("GET", "/api/v1/targets")
        return response.get("data", {})

    async def get_alerts(self) -> list[dict[str, Any]]:
        """Get active alerts.

        Returns:
            list[dict[str, Any]]: List of active alerts.
        """
        response = await self._async_request("GET", "/api/v1/alerts")
        return response.get("data", {}).get("alerts", [])

    async def health_check(self) -> bool:
        """Check Prometheus connectivity.

        Returns:
            bool: True if Prometheus is reachable, False otherwise.
        """
        try:
            response = await self._async_request("GET", "/-/healthy")
            return response.status_code == 200
        except Exception:
            return False

    async def _async_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an async HTTP request to Prometheus.

        Args:
            method: HTTP method.
            path: API path.
            params: Optional query parameters.

        Returns:
            dict[str, Any]: JSON response data.

        Raises:
            RuntimeError: If the async client is not connected.
            httpx.HTTPError: If the request fails.
        """
        if self._async_client is None:
            raise RuntimeError("Prometheus client not connected. Call connect() first.")

        response = await self._async_client.request(
            method=method,
            url=path,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def _parse_query_response(self, response: dict[str, Any]) -> list[QueryResult]:
        """Parse Prometheus query response into QueryResult objects.

        Args:
            response: Raw Prometheus API response.

        Returns:
            list[QueryResult]: Parsed query results.
        """
        data = response.get("data", {})
        result_type = data.get("resultType", "")
        results = data.get("result", [])

        parsed_results: list[QueryResult] = []

        for result in results:
            metric_data = result.get("metric", {})
            metric_name = metric_data.get("__name__", "unknown")
            labels = {k: v for k, v in metric_data.items() if not k.startswith("__")}

            if result_type == "matrix":
                # Range query result
                values = result.get("values", [])
                metric_values = [
                    MetricValue(
                        timestamp=datetime.fromtimestamp(ts),
                        value=float(val),
                        labels=labels,
                    )
                    for ts, val in values
                ]
                parsed_results.append(
                    QueryResult(
                        metric_name=metric_name,
                        labels=labels,
                        values=metric_values,
                    )
                )
            elif result_type == "vector":
                # Instant query result
                value_data = result.get("value", [])
                if value_data:
                    metric_value = MetricValue(
                        timestamp=datetime.fromtimestamp(value_data[0]),
                        value=float(value_data[1]),
                        labels=labels,
                    )
                    parsed_results.append(
                        QueryResult(
                            metric_name=metric_name,
                            labels=labels,
                            value=metric_value,
                        )
                    )
            elif result_type == "scalar":
                # Scalar result
                value_data = result.get("value", [])
                if value_data:
                    metric_value = MetricValue(
                        timestamp=datetime.fromtimestamp(value_data[0]),
                        value=float(value_data[1]),
                        labels={},
                    )
                    parsed_results.append(
                        QueryResult(
                            metric_name="scalar",
                            labels={},
                            value=metric_value,
                        )
                    )

        return parsed_results


# Global Prometheus client instance
_prometheus_client: PrometheusClient | None = None


async def init_prometheus_client() -> PrometheusClient:
    """Initialize the global Prometheus client.

    Returns:
        PrometheusClient: The initialized Prometheus client instance.
    """
    global _prometheus_client
    if _prometheus_client is None:
        _prometheus_client = PrometheusClient()
        await _prometheus_client.connect()
    return _prometheus_client


async def close_prometheus_client() -> None:
    """Close the global Prometheus client."""
    global _prometheus_client
    if _prometheus_client is not None:
        await _prometheus_client.close()
        _prometheus_client = None


def get_prometheus_client() -> PrometheusClient:
    """Get the global Prometheus client instance.

    Raises:
        RuntimeError: If the client has not been initialized.

    Returns:
        PrometheusClient: The global Prometheus client instance.
    """
    if _prometheus_client is None:
        raise RuntimeError("Prometheus client not initialized. Call init_prometheus_client() first.")
    return _prometheus_client

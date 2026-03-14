"""Metrics query API endpoints for NyxAI.

This module provides REST API endpoints for querying Prometheus metrics,
including instant queries, range queries, and metadata retrieval.
"""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, status

from nyxai.api.dependencies import PrometheusDep
from nyxai.api.models.metrics import (
    LabelsResponse,
    LabelValuesResponse,
    MetricNamesResponse,
    QueryRangeResponse,
    QueryResponse,
)

router = APIRouter()


@router.get(
    "/metrics/query",
    response_model=QueryResponse,
    summary="Execute PromQL query",
    description="Execute an instant PromQL query against Prometheus.",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid query"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Prometheus unavailable"},
    },
)
async def query_metrics(
    prometheus: PrometheusDep,
    query: Annotated[str, Query(..., description="PromQL query string", min_length=1)],
    time: Annotated[datetime | None, Query(description="Optional timestamp for the query")] = None,
) -> QueryResponse:
    """Execute an instant PromQL query.

    Args:
        prometheus: Prometheus client dependency.
        query: The PromQL query string.
        time: Optional timestamp for the query.

    Returns:
        QueryResponse: The query results.

    Raises:
        HTTPException: If the query fails or Prometheus is unavailable.
    """
    try:
        results = await prometheus.query(query, time=time)

        # Convert results to dictionary format
        result_data: dict[str, Any] = {
            "resultType": "vector",
            "result": [],
        }

        for result in results:
            metric_entry: dict[str, Any] = {
                "metric": {"__name__": result.metric_name, **result.labels},
            }

            if result.value:
                metric_entry["value"] = [
                    result.value.timestamp.timestamp(),
                    str(result.value.value),
                ]

            result_data["result"].append(metric_entry)

        return QueryResponse(
            status="success",
            data=result_data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query failed: {e!s}",
        ) from e


@router.get(
    "/metrics/query_range",
    response_model=QueryRangeResponse,
    summary="Execute range query",
    description="Execute a range PromQL query against Prometheus.",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid query"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Prometheus unavailable"},
    },
)
async def query_metrics_range(
    prometheus: PrometheusDep,
    query: Annotated[str, Query(..., description="PromQL query string", min_length=1)],
    start: Annotated[datetime, Query(..., description="Start time for the query range")],
    end: Annotated[datetime, Query(..., description="End time for the query range")],
    step: Annotated[str, Query(description="Query resolution step width", default="15s")] = "15s",
) -> QueryRangeResponse:
    """Execute a range PromQL query.

    Args:
        prometheus: Prometheus client dependency.
        query: The PromQL query string.
        start: Start time for the query range.
        end: End time for the query range.
        step: Query resolution step width (e.g., '1m', '5m', '1h').

    Returns:
        QueryRangeResponse: The query results with time series data.

    Raises:
        HTTPException: If the query fails or Prometheus is unavailable.
    """
    try:
        results = await prometheus.query_range(query, start=start, end=end, step=step)

        # Convert results to dictionary format
        result_data: dict[str, Any] = {
            "resultType": "matrix",
            "result": [],
        }

        for result in results:
            metric_entry: dict[str, Any] = {
                "metric": {"__name__": result.metric_name, **result.labels},
            }

            if result.values:
                metric_entry["values"] = [
                    [v.timestamp.timestamp(), str(v.value)] for v in result.values
                ]

            result_data["result"].append(metric_entry)

        return QueryRangeResponse(
            status="success",
            data=result_data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Range query failed: {e!s}",
        ) from e


@router.get(
    "/metrics/labels",
    response_model=LabelsResponse,
    summary="Get label names",
    description="Get a list of all label names from Prometheus.",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Prometheus unavailable"},
    },
)
async def get_labels(
    prometheus: PrometheusDep,
    start: Annotated[datetime | None, Query(description="Optional start time")] = None,
    end: Annotated[datetime | None, Query(description="Optional end time")] = None,
) -> LabelsResponse:
    """Get all label names from Prometheus.

    Args:
        prometheus: Prometheus client dependency.
        start: Optional start time for filtering.
        end: Optional end time for filtering.

    Returns:
        LabelsResponse: List of label names.

    Raises:
        HTTPException: If Prometheus is unavailable.
    """
    try:
        # Use the series endpoint to get labels
        series = await prometheus.get_series(start=start, end=end)

        # Extract unique label names
        label_names: set[str] = set()
        for s in series:
            label_names.update(s.keys())

        return LabelsResponse(
            status="success",
            data=sorted(label_names),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get labels: {e!s}",
        ) from e


@router.get(
    "/metrics/label_values",
    response_model=LabelValuesResponse,
    summary="Get label values",
    description="Get all values for a specific label from Prometheus.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Label not found"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Prometheus unavailable"},
    },
)
async def get_label_values(
    prometheus: PrometheusDep,
    label: Annotated[str, Query(..., description="Label name", min_length=1)],
) -> LabelValuesResponse:
    """Get all values for a specific label.

    Args:
        prometheus: Prometheus client dependency.
        label: The label name.

    Returns:
        LabelValuesResponse: List of label values.

    Raises:
        HTTPException: If the label doesn't exist or Prometheus is unavailable.
    """
    try:
        values = await prometheus.get_label_values(label)

        return LabelValuesResponse(
            status="success",
            data=values,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get label values: {e!s}",
        ) from e


@router.get(
    "/metrics/names",
    response_model=MetricNamesResponse,
    summary="Get metric names",
    description="Get a list of all available metric names from Prometheus.",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Prometheus unavailable"},
    },
)
async def get_metric_names(
    prometheus: PrometheusDep,
) -> MetricNamesResponse:
    """Get all available metric names from Prometheus.

    Args:
        prometheus: Prometheus client dependency.

    Returns:
        MetricNamesResponse: List of metric names.

    Raises:
        HTTPException: If Prometheus is unavailable.
    """
    try:
        # Get metadata which includes metric names
        metadata = await prometheus.get_metric_metadata()

        # Extract metric names
        metric_names = list(metadata.keys())

        return MetricNamesResponse(
            status="success",
            data=sorted(metric_names),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get metric names: {e!s}",
        ) from e


@router.get(
    "/metrics/series",
    summary="Get series",
    description="Get time series that match the given label selectors.",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid match expression"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Prometheus unavailable"},
    },
)
async def get_series(
    prometheus: PrometheusDep,
    match: Annotated[list[str] | None, Query(description="Series selectors")] = None,
    start: Annotated[datetime | None, Query(description="Optional start time")] = None,
    end: Annotated[datetime | None, Query(description="Optional end time")] = None,
) -> dict[str, Any]:
    """Get time series matching the given label selectors.

    Args:
        prometheus: Prometheus client dependency.
        match: List of series selectors.
        start: Optional start time.
        end: Optional end time.

    Returns:
        Dictionary with series data.

    Raises:
        HTTPException: If the query fails or Prometheus is unavailable.
    """
    try:
        series = await prometheus.get_series(match=match, start=start, end=end)

        return {
            "status": "success",
            "data": series,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get series: {e!s}",
        ) from e

"""Anomaly management API endpoints for NyxAI.

This module provides REST API endpoints for managing anomalies, including
listing, creating, updating, and resolving anomalies.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from nyxai.api.models.anomaly import (
    AnomalyActionResponse,
    AnomalyCreateRequest,
    AnomalyFilterParams,
    AnomalyListResponse,
    AnomalyResponse,
    AnomalyUpdateRequest,
)
from nyxai.api.models.common import PaginationParams
from nyxai.detection.models.anomaly import Anomaly, AnomalySeverity, AnomalyStatus

router = APIRouter()

# In-memory storage for demonstration (replace with database in production)
_anomalies: dict[str, Anomaly] = {}


@router.get(
    "/anomalies",
    response_model=AnomalyListResponse,
    summary="List anomalies",
    description="Get a paginated list of anomalies with optional filtering.",
)
async def list_anomalies(
    pagination: Annotated[PaginationParams, Query()],
    filters: Annotated[AnomalyFilterParams, Query()],
) -> AnomalyListResponse:
    """Get a list of anomalies with pagination and filtering.

    Args:
        pagination: Pagination parameters (page, page_size).
        filters: Filter parameters for severity, status, etc.

    Returns:
        AnomalyListResponse: Paginated list of anomalies.
    """
    # Filter anomalies
    filtered = list(_anomalies.values())

    if filters.severity:
        filtered = [a for a in filtered if a.severity == filters.severity]

    if filters.status:
        filtered = [a for a in filtered if a.status == filters.status]

    if filters.source_type:
        filtered = [a for a in filtered if a.source_type == filters.source_type]

    if filters.detection_method:
        filtered = [a for a in filtered if a.detection_method == filters.detection_method]

    if filters.assigned_to:
        filtered = [a for a in filtered if a.assigned_to == filters.assigned_to]

    if filters.tags:
        tag_list = [t.strip() for t in filters.tags.split(",")]
        filtered = [a for a in filtered if any(t in a.tags for t in tag_list)]

    if filters.start_date:
        filtered = [a for a in filtered if a.detected_at >= filters.start_date]

    if filters.end_date:
        filtered = [a for a in filtered if a.detected_at <= filters.end_date]

    # Sort by detected_at descending
    filtered.sort(key=lambda a: a.detected_at, reverse=True)

    # Calculate pagination
    total = len(filtered)
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    offset = pagination.offset
    paginated = filtered[offset : offset + pagination.page_size]

    # Convert to response models
    items = [AnomalyResponse.model_validate(a) for a in paginated]

    return AnomalyListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get(
    "/anomalies/{anomaly_id}",
    response_model=AnomalyResponse,
    summary="Get anomaly details",
    description="Get detailed information about a specific anomaly.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Anomaly not found"},
    },
)
async def get_anomaly(anomaly_id: str) -> AnomalyResponse:
    """Get details of a specific anomaly.

    Args:
        anomaly_id: The unique identifier of the anomaly.

    Returns:
        AnomalyResponse: The anomaly details.

    Raises:
        HTTPException: If the anomaly is not found.
    """
    if anomaly_id not in _anomalies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly with ID '{anomaly_id}' not found",
        )

    return AnomalyResponse.model_validate(_anomalies[anomaly_id])


@router.post(
    "/anomalies",
    response_model=AnomalyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create anomaly",
    description="Create a new anomaly record.",
)
async def create_anomaly(request: AnomalyCreateRequest) -> AnomalyResponse:
    """Create a new anomaly.

    Args:
        request: The anomaly creation request.

    Returns:
        AnomalyResponse: The created anomaly.
    """
    # Determine severity from score if not provided
    severity = request.severity
    if severity is None:
        severity = AnomalySeverity.from_score(request.score)

    # Create the anomaly
    anomaly = Anomaly.create(
        title=request.title,
        description=request.description,
        severity=severity,
        source_type=request.source_type,
        detection_method=request.detection_method,
        score=request.score,
        confidence=request.confidence,
        metadata=request.metadata,
        tags=request.tags,
    )

    # Set assigned_to if provided
    if request.assigned_to:
        anomaly.assigned_to = request.assigned_to

    # Store the anomaly
    _anomalies[anomaly.id] = anomaly

    return AnomalyResponse.model_validate(anomaly)


@router.put(
    "/anomalies/{anomaly_id}",
    response_model=AnomalyResponse,
    summary="Update anomaly",
    description="Update an existing anomaly record.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Anomaly not found"},
    },
)
async def update_anomaly(
    anomaly_id: str,
    request: AnomalyUpdateRequest,
) -> AnomalyResponse:
    """Update an existing anomaly.

    Args:
        anomaly_id: The unique identifier of the anomaly.
        request: The update request with fields to modify.

    Returns:
        AnomalyResponse: The updated anomaly.

    Raises:
        HTTPException: If the anomaly is not found.
    """
    if anomaly_id not in _anomalies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly with ID '{anomaly_id}' not found",
        )

    anomaly = _anomalies[anomaly_id]

    # Update fields if provided
    if request.title is not None:
        anomaly.title = request.title

    if request.description is not None:
        anomaly.description = request.description

    if request.severity is not None:
        anomaly.severity = request.severity

    if request.status is not None:
        anomaly.status = request.status
        # Update resolved_at if status is resolved
        if request.status in (AnomalyStatus.RESOLVED, AnomalyStatus.FALSE_POSITIVE):
            anomaly.resolved_at = datetime.utcnow()

    if request.metadata is not None:
        anomaly.metadata = request.metadata

    if request.tags is not None:
        anomaly.tags = request.tags

    if request.assigned_to is not None:
        anomaly.assigned_to = request.assigned_to

    return AnomalyResponse.model_validate(anomaly)


@router.post(
    "/anomalies/{anomaly_id}/acknowledge",
    response_model=AnomalyActionResponse,
    summary="Acknowledge anomaly",
    description="Acknowledge an anomaly to indicate it has been seen.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Anomaly not found"},
    },
)
async def acknowledge_anomaly(anomaly_id: str) -> AnomalyActionResponse:
    """Acknowledge an anomaly.

    Args:
        anomaly_id: The unique identifier of the anomaly.

    Returns:
        AnomalyActionResponse: The result of the acknowledgment.

    Raises:
        HTTPException: If the anomaly is not found.
    """
    if anomaly_id not in _anomalies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly with ID '{anomaly_id}' not found",
        )

    anomaly = _anomalies[anomaly_id]
    anomaly.acknowledge()

    return AnomalyActionResponse(
        success=True,
        anomaly=AnomalyResponse.model_validate(anomaly),
        message="Anomaly acknowledged successfully",
    )


@router.post(
    "/anomalies/{anomaly_id}/resolve",
    response_model=AnomalyActionResponse,
    summary="Resolve anomaly",
    description="Mark an anomaly as resolved.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Anomaly not found"},
    },
)
async def resolve_anomaly(anomaly_id: str) -> AnomalyActionResponse:
    """Resolve an anomaly.

    Args:
        anomaly_id: The unique identifier of the anomaly.

    Returns:
        AnomalyActionResponse: The result of the resolution.

    Raises:
        HTTPException: If the anomaly is not found.
    """
    if anomaly_id not in _anomalies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly with ID '{anomaly_id}' not found",
        )

    anomaly = _anomalies[anomaly_id]
    anomaly.resolve()

    return AnomalyActionResponse(
        success=True,
        anomaly=AnomalyResponse.model_validate(anomaly),
        message="Anomaly resolved successfully",
    )


@router.post(
    "/anomalies/{anomaly_id}/ignore",
    response_model=AnomalyActionResponse,
    summary="Ignore anomaly",
    description="Mark an anomaly as ignored/false positive.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Anomaly not found"},
    },
)
async def ignore_anomaly(anomaly_id: str) -> AnomalyActionResponse:
    """Ignore an anomaly.

    Args:
        anomaly_id: The unique identifier of the anomaly.

    Returns:
        AnomalyActionResponse: The result of the ignore action.

    Raises:
        HTTPException: If the anomaly is not found.
    """
    if anomaly_id not in _anomalies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly with ID '{anomaly_id}' not found",
        )

    anomaly = _anomalies[anomaly_id]
    from nyxai.detection.models.anomaly import AnomalyStatus
    anomaly.status = AnomalyStatus.FALSE_POSITIVE
    anomaly.resolved_at = datetime.utcnow()

    return AnomalyActionResponse(
        success=True,
        anomaly=AnomalyResponse.model_validate(anomaly),
        message="Anomaly ignored successfully",
    )

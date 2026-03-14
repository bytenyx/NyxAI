"""API request and response models for NyxAI.

This module contains Pydantic models for API request validation and response serialization.
"""

from nyxai.api.models.anomaly import (
    AnomalyCreateRequest,
    AnomalyListResponse,
    AnomalyResponse,
    AnomalyUpdateRequest,
)
from nyxai.api.models.common import (
    APIResponse,
    ErrorResponse,
    HealthCheckResponse,
    PaginationParams,
)
from nyxai.api.models.metrics import (
    LabelsResponse,
    LabelValuesResponse,
    MetricNamesResponse,
    QueryRangeResponse,
    QueryResponse,
)

__all__ = [
    # Common models
    "APIResponse",
    "ErrorResponse",
    "HealthCheckResponse",
    "PaginationParams",
    # Anomaly models
    "AnomalyCreateRequest",
    "AnomalyListResponse",
    "AnomalyResponse",
    "AnomalyUpdateRequest",
    # Metrics models
    "LabelValuesResponse",
    "LabelsResponse",
    "MetricNamesResponse",
    "QueryRangeResponse",
    "QueryResponse",
]

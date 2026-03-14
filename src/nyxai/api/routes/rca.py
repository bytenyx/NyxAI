"""Root Cause Analysis API endpoints for NyxAI.

This module provides REST API endpoints for root cause analysis,
including service topology and impact analysis.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from nyxai.rca.topology.service_graph import ServiceGraph, ServiceNode, ServiceStatus

router = APIRouter()

# Shared service graph instance (in production, this would be injected)
_service_graph: ServiceGraph | None = None


def get_service_graph() -> ServiceGraph:
    """Get or create the service graph instance."""
    global _service_graph
    if _service_graph is None:
        _service_graph = ServiceGraph()
    return _service_graph


class ServiceNodeRequest(BaseModel):
    """Request model for creating a service node."""

    id: str
    name: str
    namespace: str = "default"
    service_type: str = "microservice"
    status: ServiceStatus = ServiceStatus.UNKNOWN
    labels: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ServiceNodeResponse(BaseModel):
    """Response model for a service node."""

    id: str
    name: str
    namespace: str
    service_type: str
    status: str
    metrics: dict[str, float]
    labels: dict[str, str]
    metadata: dict[str, Any]


class ServiceDependencyRequest(BaseModel):
    """Request model for creating a service dependency."""

    source_id: str
    target_id: str
    dependency_type: str = "sync"
    latency_ms: float = 0.0
    error_rate: float = 0.0
    call_volume: float = 0.0


class RootCauseAnalysisRequest(BaseModel):
    """Request model for root cause analysis."""

    service_id: str
    anomaly_score: float = Field(default=1.0, ge=0.0, le=1.0)


class RootCauseAnalysisResponse(BaseModel):
    """Response model for root cause analysis."""

    service_id: str
    root_causes: list[dict[str, Any]]
    upstream_services: dict[str, int]
    downstream_services: dict[str, int]


class ImpactAnalysisRequest(BaseModel):
    """Request model for impact analysis."""

    service_id: str
    fault_probability: float = Field(default=1.0, ge=0.0, le=1.0)


class ImpactAnalysisResponse(BaseModel):
    """Response model for impact analysis."""

    service_id: str
    propagation: dict[str, float]
    total_affected: int


@router.post(
    "/rca/services",
    response_model=ServiceNodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register service",
    description="Register a new service in the topology graph.",
)
async def register_service(request: ServiceNodeRequest) -> ServiceNodeResponse:
    """Register a new service."""
    graph = get_service_graph()

    node = ServiceNode(
        id=request.id,
        name=request.name,
        namespace=request.namespace,
        service_type=request.service_type,
        status=request.status,
        labels=request.labels,
        metadata=request.metadata,
    )

    graph.add_service(node)

    return ServiceNodeResponse.model_validate(node.to_dict())


@router.get(
    "/rca/services/{service_id}",
    response_model=ServiceNodeResponse,
    summary="Get service details",
    description="Get details of a registered service.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Service not found"},
    },
)
async def get_service(service_id: str) -> ServiceNodeResponse:
    """Get service details."""
    graph = get_service_graph()

    service = graph.get_service(service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_id}' not found",
        )

    return ServiceNodeResponse.model_validate(service.to_dict())


@router.delete(
    "/rca/services/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unregister service",
    description="Remove a service from the topology graph.",
)
async def unregister_service(service_id: str) -> None:
    """Unregister a service."""
    graph = get_service_graph()
    graph.remove_service(service_id)


@router.post(
    "/rca/dependencies",
    status_code=status.HTTP_201_CREATED,
    summary="Add dependency",
    description="Add a dependency between two services.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Source or target service not found"},
    },
)
async def add_dependency(request: ServiceDependencyRequest) -> dict[str, str]:
    """Add a service dependency."""
    graph = get_service_graph()

    try:
        from nyxai.rca.topology.service_graph import ServiceEdge, DependencyType

        edge = ServiceEdge(
            source_id=request.source_id,
            target_id=request.target_id,
            dependency_type=DependencyType(request.dependency_type),
            latency_ms=request.latency_ms,
            error_rate=request.error_rate,
            call_volume=request.call_volume,
        )

        graph.add_dependency(request.source_id, request.target_id, edge)

        return {"message": "Dependency added successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/rca/services/{service_id}/dependencies",
    summary="Get service dependencies",
    description="Get the direct dependencies of a service.",
)
async def get_service_dependencies(service_id: str) -> list[str]:
    """Get service dependencies."""
    graph = get_service_graph()

    if not graph.get_service(service_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_id}' not found",
        )

    return graph.get_dependencies(service_id)


@router.get(
    "/rca/services/{service_id}/dependents",
    summary="Get service dependents",
    description="Get services that depend on this service.",
)
async def get_service_dependents(service_id: str) -> list[str]:
    """Get service dependents."""
    graph = get_service_graph()

    if not graph.get_service(service_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_id}' not found",
        )

    return graph.get_dependents(service_id)


@router.post(
    "/rca/analyze",
    response_model=RootCauseAnalysisResponse,
    summary="Analyze root causes",
    description="Perform root cause analysis for a service.",
)
async def analyze_root_causes(
    request: RootCauseAnalysisRequest,
) -> RootCauseAnalysisResponse:
    """Analyze root causes."""
    graph = get_service_graph()

    if not graph.get_service(request.service_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{request.service_id}' not found",
        )

    # Find root causes
    root_causes = graph.find_root_causes(request.service_id, request.anomaly_score)

    # Get upstream and downstream services
    upstream = graph.get_upstream_services(request.service_id)
    downstream = graph.get_downstream_services(request.service_id)

    return RootCauseAnalysisResponse(
        service_id=request.service_id,
        root_causes=root_causes,
        upstream_services=upstream,
        downstream_services=downstream,
    )


@router.post(
    "/rca/impact",
    response_model=ImpactAnalysisResponse,
    summary="Analyze impact",
    description="Analyze the impact of a fault on the system.",
)
async def analyze_impact(request: ImpactAnalysisRequest) -> ImpactAnalysisResponse:
    """Analyze fault impact."""
    graph = get_service_graph()

    if not graph.get_service(request.service_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{request.service_id}' not found",
        )

    # Analyze fault propagation
    propagation = graph.analyze_fault_propagation(
        request.service_id, request.fault_probability
    )

    return ImpactAnalysisResponse(
        service_id=request.service_id,
        propagation=propagation,
        total_affected=len(propagation),
    )


@router.get(
    "/rca/topology",
    summary="Get topology",
    description="Get the complete service topology.",
)
async def get_topology() -> dict[str, Any]:
    """Get service topology."""
    graph = get_service_graph()
    return graph.to_dict()


@router.get(
    "/rca/topology/summary",
    summary="Get topology summary",
    description="Get summary statistics of the topology.",
)
async def get_topology_summary() -> dict[str, Any]:
    """Get topology summary."""
    graph = get_service_graph()
    return graph.get_topology_summary()


@router.get(
    "/rca/services/{service_id}/impact-score",
    summary="Get impact score",
    description="Get the impact score of a service.",
)
async def get_impact_score(service_id: str) -> dict[str, Any]:
    """Get service impact score."""
    graph = get_service_graph()

    if not graph.get_service(service_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_id}' not found",
        )

    score = graph.get_service_impact_score(service_id)

    return {
        "service_id": service_id,
        "impact_score": score,
    }

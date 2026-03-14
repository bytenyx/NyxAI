"""Service topology graph for NyxAI RCA.

This module implements service dependency graph and topology analysis
for root cause analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import networkx as nx
import numpy as np
from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Service health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class DependencyType(str, Enum):
    """Type of service dependency."""

    SYNC = "sync"  # Synchronous call
    ASYNC = "async"  # Asynchronous call
    DATABASE = "database"  # Database dependency
    CACHE = "cache"  # Cache dependency
    MESSAGE_QUEUE = "message_queue"  # Message queue dependency
    EXTERNAL = "external"  # External service dependency


@dataclass
class ServiceNode:
    """Represents a service node in the topology graph.

    Attributes:
        id: Unique identifier for the service.
        name: Human-readable name of the service.
        namespace: Kubernetes namespace or environment.
        service_type: Type of service (e.g., 'microservice', 'database').
        status: Current health status of the service.
        metrics: Current service metrics.
        labels: Additional metadata labels.
        metadata: Additional service metadata.
    """

    id: str
    name: str
    namespace: str = "default"
    service_type: str = "microservice"
    status: ServiceStatus = ServiceStatus.UNKNOWN
    metrics: dict[str, float] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def update_status(self, status: ServiceStatus) -> None:
        """Update the service status.

        Args:
            status: New status to set.
        """
        self.status = status

    def update_metrics(self, metrics: dict[str, float]) -> None:
        """Update service metrics.

        Args:
            metrics: New metrics to set.
        """
        self.metrics.update(metrics)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the service node.
        """
        return {
            "id": self.id,
            "name": self.name,
            "namespace": self.namespace,
            "service_type": self.service_type,
            "status": self.status.value,
            "metrics": self.metrics,
            "labels": self.labels,
            "metadata": self.metadata,
        }


@dataclass
class ServiceEdge:
    """Represents a dependency edge between services.

    Attributes:
        source_id: ID of the source service.
        target_id: ID of the target service.
        dependency_type: Type of dependency.
        latency_ms: Average latency in milliseconds.
        error_rate: Error rate for this connection.
        call_volume: Request volume.
        weight: Edge weight for path calculations.
        metadata: Additional edge metadata.
    """

    source_id: str
    target_id: str
    dependency_type: DependencyType = DependencyType.SYNC
    latency_ms: float = 0.0
    error_rate: float = 0.0
    call_volume: float = 0.0
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the edge.
        """
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "dependency_type": self.dependency_type.value,
            "latency_ms": self.latency_ms,
            "error_rate": self.error_rate,
            "call_volume": self.call_volume,
            "weight": self.weight,
            "metadata": self.metadata,
        }


class ServiceGraphConfig(BaseModel):
    """Configuration for ServiceGraph.

    Attributes:
        max_hops: Maximum number of hops for path analysis.
        min_confidence: Minimum confidence for root cause attribution.
        propagation_factor: Factor for fault propagation scoring.
    """

    max_hops: int = Field(default=5, ge=1, description="Maximum hops for analysis")
    min_confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )
    propagation_factor: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Fault propagation factor"
    )


class ServiceGraph:
    """Service topology graph for root cause analysis.

    This class manages the service dependency graph and provides methods
    for topology analysis, fault propagation, and root cause identification.

    Attributes:
        config: ServiceGraph configuration.
        _graph: Internal NetworkX directed graph.
    """

    def __init__(self, config: ServiceGraphConfig | None = None) -> None:
        """Initialize the service graph.

        Args:
            config: Configuration for the graph. Uses defaults if None.
        """
        self.config = config or ServiceGraphConfig()
        self._graph: nx.DiGraph = nx.DiGraph()

    def add_service(self, node: ServiceNode) -> None:
        """Add a service node to the graph.

        Args:
            node: Service node to add.
        """
        self._graph.add_node(
            node.id,
            data=node,
            **node.to_dict(),
        )

    def add_dependency(
        self,
        source_id: str,
        target_id: str,
        edge: ServiceEdge | None = None,
    ) -> None:
        """Add a dependency edge between services.

        Args:
            source_id: ID of the source service.
            target_id: ID of the target service.
            edge: Edge data. Creates default edge if None.

        Raises:
            ValueError: If source or target service doesn't exist.
        """
        if source_id not in self._graph:
            raise ValueError(f"Source service '{source_id}' not found")
        if target_id not in self._graph:
            raise ValueError(f"Target service '{target_id}' not found")

        if edge is None:
            edge = ServiceEdge(source_id=source_id, target_id=target_id)

        self._graph.add_edge(
            source_id,
            target_id,
            data=edge,
            **edge.to_dict(),
        )

    def remove_service(self, service_id: str) -> None:
        """Remove a service from the graph.

        Args:
            service_id: ID of the service to remove.
        """
        if service_id in self._graph:
            self._graph.remove_node(service_id)

    def remove_dependency(self, source_id: str, target_id: str) -> None:
        """Remove a dependency edge.

        Args:
            source_id: ID of the source service.
            target_id: ID of the target service.
        """
        if self._graph.has_edge(source_id, target_id):
            self._graph.remove_edge(source_id, target_id)

    def get_service(self, service_id: str) -> ServiceNode | None:
        """Get a service node by ID.

        Args:
            service_id: ID of the service.

        Returns:
            Service node if found, None otherwise.
        """
        if service_id in self._graph:
            return self._graph.nodes[service_id].get("data")
        return None

    def get_dependencies(self, service_id: str) -> list[str]:
        """Get direct dependencies of a service.

        Args:
            service_id: ID of the service.

        Returns:
            List of dependency service IDs.
        """
        if service_id not in self._graph:
            return []
        return list(self._graph.successors(service_id))

    def get_dependents(self, service_id: str) -> list[str]:
        """Get services that depend on this service.

        Args:
            service_id: ID of the service.

        Returns:
            List of dependent service IDs.
        """
        if service_id not in self._graph:
            return []
        return list(self._graph.predecessors(service_id))

    def get_upstream_services(
        self,
        service_id: str,
        max_hops: int | None = None,
    ) -> dict[str, int]:
        """Get all upstream services within max_hops.

        Args:
            service_id: ID of the service.
            max_hops: Maximum number of hops. Uses config default if None.

        Returns:
            Dictionary mapping service ID to hop distance.
        """
        if service_id not in self._graph:
            return {}

        max_hops = max_hops or self.config.max_hops
        upstream = {}

        for target in self._graph.nodes():
            if target == service_id:
                continue
            try:
                path = nx.shortest_path(
                    self._graph, target, service_id, weight="weight"
                )
                hops = len(path) - 1
                if hops <= max_hops:
                    upstream[target] = hops
            except nx.NetworkXNoPath:
                continue

        return upstream

    def get_downstream_services(
        self,
        service_id: str,
        max_hops: int | None = None,
    ) -> dict[str, int]:
        """Get all downstream services within max_hops.

        Args:
            service_id: ID of the service.
            max_hops: Maximum number of hops. Uses config default if None.

        Returns:
            Dictionary mapping service ID to hop distance.
        """
        if service_id not in self._graph:
            return {}

        max_hops = max_hops or self.config.max_hops
        downstream = {}

        for target in self._graph.nodes():
            if target == service_id:
                continue
            try:
                path = nx.shortest_path(
                    self._graph, service_id, target, weight="weight"
                )
                hops = len(path) - 1
                if hops <= max_hops:
                    downstream[target] = hops
            except nx.NetworkXNoPath:
                continue

        return downstream

    def find_root_causes(
        self,
        affected_service: str,
        anomaly_score: float = 1.0,
    ) -> list[dict[str, Any]]:
        """Find potential root causes for an affected service.

        This method analyzes the service topology to identify potential
        root cause services based on:
        - Upstream dependency paths
        - Service health status
        - Fault propagation probability

        Args:
            affected_service: ID of the affected service.
            anomaly_score: Severity of the anomaly (0.0 to 1.0).

        Returns:
            List of potential root causes with confidence scores.
        """
        if affected_service not in self._graph:
            return []

        upstream = self.get_upstream_services(affected_service)
        if not upstream:
            return []

        candidates = []

        for service_id, hops in upstream.items():
            service = self.get_service(service_id)
            if service is None:
                continue

            # Calculate confidence based on multiple factors
            confidence = self._calculate_root_cause_confidence(
                service=service,
                hops=hops,
                anomaly_score=anomaly_score,
            )

            if confidence >= self.config.min_confidence:
                candidates.append({
                    "service_id": service_id,
                    "service_name": service.name,
                    "hops": hops,
                    "confidence": confidence,
                    "status": service.status.value,
                    "metrics": service.metrics,
                })

        # Sort by confidence (descending)
        candidates.sort(key=lambda x: x["confidence"], reverse=True)

        return candidates

    def _calculate_root_cause_confidence(
        self,
        service: ServiceNode,
        hops: int,
        anomaly_score: float,
    ) -> float:
        """Calculate confidence score for a root cause candidate.

        Args:
            service: Service node to evaluate.
            hops: Distance from affected service.
            anomaly_score: Severity of the anomaly.

        Returns:
            Confidence score (0.0 to 1.0).
        """
        # Base confidence from distance (closer = higher confidence)
        distance_factor = self.config.propagation_factor ** hops

        # Status factor (unhealthy services are more likely root causes)
        status_weights = {
            ServiceStatus.UNHEALTHY: 1.0,
            ServiceStatus.DEGRADED: 0.7,
            ServiceStatus.UNKNOWN: 0.4,
            ServiceStatus.HEALTHY: 0.1,
        }
        status_factor = status_weights.get(service.status, 0.0)

        # Metric anomaly factor
        metric_factor = 0.0
        if service.metrics:
            # Check for anomalous metrics
            error_rate = service.metrics.get("error_rate", 0)
            latency_p99 = service.metrics.get("latency_p99", 0)
            cpu_usage = service.metrics.get("cpu_usage", 0)

            # Normalize and combine metrics
            metric_scores = []
            if error_rate > 0:
                metric_scores.append(min(error_rate * 5, 1.0))
            if latency_p99 > 0:
                metric_scores.append(min(latency_p99 / 1000, 1.0))
            if cpu_usage > 0:
                metric_scores.append(min(cpu_usage / 100, 1.0))

            if metric_scores:
                metric_factor = np.mean(metric_scores)

        # Combine factors
        confidence = (
            0.4 * distance_factor +
            0.3 * status_factor +
            0.2 * metric_factor +
            0.1 * anomaly_score
        )

        return float(np.clip(confidence, 0.0, 1.0))

    def analyze_fault_propagation(
        self,
        root_service: str,
        fault_probability: float = 1.0,
    ) -> dict[str, float]:
        """Analyze how a fault propagates through the system.

        Args:
            root_service: ID of the service where fault originates.
            fault_probability: Initial fault probability.

        Returns:
            Dictionary mapping service ID to fault probability.
        """
        if root_service not in self._graph:
            return {}

        propagation = {root_service: fault_probability}
        visited = {root_service}
        queue = [(root_service, fault_probability, 0)]

        while queue:
            current, prob, hops = queue.pop(0)

            if hops >= self.config.max_hops:
                continue

            # Propagate to downstream services
            for successor in self._graph.successors(current):
                edge_data = self._graph.edges[current, successor]

                # Calculate propagation probability based on edge properties
                edge_weight = edge_data.get("weight", 1.0)
                error_rate = edge_data.get("error_rate", 0.0)

                # Higher error rate and weight = higher propagation
                propagation_prob = prob * (
                    self.config.propagation_factor *
                    (1 + error_rate) *
                    edge_weight
                )
                propagation_prob = min(propagation_prob, 1.0)

                if successor not in propagation:
                    propagation[successor] = 0.0

                # Combine probabilities (use max for conservative estimate)
                propagation[successor] = max(
                    propagation[successor],
                    propagation_prob,
                )

                if successor not in visited:
                    visited.add(successor)
                    queue.append((successor, propagation_prob, hops + 1))

        return propagation

    def get_critical_path(
        self,
        source: str,
        target: str,
    ) -> list[str] | None:
        """Find the critical path between two services.

        Args:
            source: Source service ID.
            target: Target service ID.

        Returns:
            List of service IDs representing the path, or None if no path.
        """
        if source not in self._graph or target not in self._graph:
            return None

        try:
            # Use Dijkstra's algorithm with latency as weight
            path = nx.shortest_path(
                self._graph,
                source,
                target,
                weight="latency_ms",
            )
            return path
        except nx.NetworkXNoPath:
            return None

    def get_service_impact_score(self, service_id: str) -> float:
        """Calculate the impact score of a service.

        Higher score means more services depend on this service.

        Args:
            service_id: ID of the service.

        Returns:
            Impact score (0.0 to 1.0).
        """
        if service_id not in self._graph:
            return 0.0

        # Count direct and indirect dependents
        dependents = self.get_dependents(service_id)
        if not dependents:
            return 0.0

        # Calculate impact based on number of dependents and their depth
        total_impact = 0.0
        visited = {service_id}
        queue = [(d, 1) for d in dependents]

        while queue:
            current, depth = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            # Impact decreases with depth
            impact = 1.0 / depth
            total_impact += impact

            # Add dependents of current service
            for d in self.get_dependents(current):
                if d not in visited:
                    queue.append((d, depth + 1))

        # Normalize impact score
        n_services = len(self._graph.nodes())
        if n_services <= 1:
            return 0.0

        return min(total_impact / (n_services - 1), 1.0)

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to dictionary representation.

        Returns:
            Dictionary with nodes and edges.
        """
        return {
            "nodes": [
                self._graph.nodes[node].get("data", {}).to_dict()
                if hasattr(self._graph.nodes[node].get("data", {}), "to_dict")
                else {"id": node}
                for node in self._graph.nodes()
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    **self._graph.edges[u, v],
                }
                for u, v in self._graph.edges()
            ],
        }

    def get_topology_summary(self) -> dict[str, Any]:
        """Get summary statistics of the topology.

        Returns:
            Dictionary with topology statistics.
        """
        n_nodes = self._graph.number_of_nodes()
        n_edges = self._graph.number_of_edges()

        if n_nodes == 0:
            return {
                "total_services": 0,
                "total_dependencies": 0,
                "avg_dependencies_per_service": 0.0,
                "is_connected": False,
            }

        # Calculate average degree
        degrees = [self._graph.degree(node) for node in self._graph.nodes()]
        avg_degree = np.mean(degrees) if degrees else 0.0

        # Check if graph is weakly connected
        is_connected = nx.is_weakly_connected(self._graph) if n_nodes > 1 else True

        # Count services by status
        status_counts = {}
        for node in self._graph.nodes():
            service = self.get_service(node)
            if service:
                status = service.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_services": n_nodes,
            "total_dependencies": n_edges,
            "avg_dependencies_per_service": avg_degree,
            "is_connected": is_connected,
            "status_distribution": status_counts,
        }

    def clear(self) -> None:
        """Clear all nodes and edges from the graph."""
        self._graph.clear()

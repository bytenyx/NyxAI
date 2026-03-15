"""Incident Knowledge Base for NyxAI.

This module provides storage and retrieval of historical incidents
with vector embedding support for similarity search using embedded ChromaDB.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

import numpy as np
from pydantic import BaseModel, Field

from nyxai.storage.vector_store import (
    EmbeddedVectorStore,
    VectorStoreConfig,
    get_vector_store,
)


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.
        """
        ...


@dataclass
class IncidentRecord:
    """Represents an incident record in the knowledge base.

    Attributes:
        id: Unique identifier for the incident.
        title: Incident title.
        description: Detailed description of the incident.
        service_id: Affected service ID.
        anomaly_type: Type of anomaly detected.
        root_cause: Identified root cause.
        solution: Solution applied to resolve the incident.
        severity: Incident severity level.
        status: Incident status.
        metrics: Relevant metrics during the incident.
        tags: Tags for categorization.
        embedding: Vector embedding of the incident.
        created_at: Incident creation timestamp.
        resolved_at: Incident resolution timestamp.
        meta_data: Additional metadata.
    """

    id: str
    title: str
    description: str
    service_id: str
    anomaly_type: str
    root_cause: str = ""
    solution: str = ""
    severity: str = "medium"
    status: str = "resolved"
    metrics: dict[str, float] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    embedding: list[float] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    meta_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the incident.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "service_id": self.service_id,
            "anomaly_type": self.anomaly_type,
            "root_cause": self.root_cause,
            "solution": self.solution,
            "severity": self.severity,
            "status": self.status,
            "metrics": self.metrics,
            "tags": self.tags,
            "embedding": self.embedding,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "meta_data": self.meta_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IncidentRecord:
        """Create an IncidentRecord from a dictionary.

        Args:
            data: Dictionary containing incident data.

        Returns:
            IncidentRecord instance.
        """
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        resolved_at = data.get("resolved_at")
        if resolved_at and isinstance(resolved_at, str):
            resolved_at = datetime.fromisoformat(resolved_at)

        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            service_id=data["service_id"],
            anomaly_type=data["anomaly_type"],
            root_cause=data.get("root_cause", ""),
            solution=data.get("solution", ""),
            severity=data.get("severity", "medium"),
            status=data.get("status", "resolved"),
            metrics=data.get("metrics", {}),
            tags=data.get("tags", []),
            embedding=data.get("embedding"),
            created_at=created_at or datetime.utcnow(),
            resolved_at=resolved_at,
            meta_data=data.get("meta_data", {}),
        )

    def generate_embedding_text(self) -> str:
        """Generate text for embedding.

        Returns:
            Combined text representation for embedding.
        """
        parts = [
            f"Title: {self.title}",
            f"Description: {self.description}",
            f"Service: {self.service_id}",
            f"Anomaly Type: {self.anomaly_type}",
            f"Root Cause: {self.root_cause}",
            f"Solution: {self.solution}",
            f"Tags: {', '.join(self.tags)}",
        ]
        return "\n".join(parts)

    def to_vector_metadata(self) -> dict[str, Any]:
        """Convert to metadata format for vector store.

        Returns:
            Dictionary suitable for vector store metadata.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "service_id": self.service_id,
            "anomaly_type": self.anomaly_type,
            "root_cause": self.root_cause,
            "solution": self.solution,
            "severity": self.severity,
            "status": self.status,
            "tags": self.tags,
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "meta_data": self.meta_data,
        }

    @classmethod
    def from_vector_metadata(
        cls,
        id: str,
        metadata: dict[str, Any],
        embedding: list[float] | None = None,
    ) -> IncidentRecord:
        """Create an IncidentRecord from vector store metadata.

        Args:
            id: Incident ID.
            metadata: Metadata from vector store.
            embedding: Optional embedding vector.

        Returns:
            IncidentRecord instance.
        """
        created_at = metadata.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        resolved_at = metadata.get("resolved_at")
        if resolved_at and isinstance(resolved_at, str):
            resolved_at = datetime.fromisoformat(resolved_at)

        return cls(
            id=id,
            title=metadata.get("title", ""),
            description=metadata.get("description", ""),
            service_id=metadata.get("service_id", ""),
            anomaly_type=metadata.get("anomaly_type", ""),
            root_cause=metadata.get("root_cause", ""),
            solution=metadata.get("solution", ""),
            severity=metadata.get("severity", "medium"),
            status=metadata.get("status", "resolved"),
            metrics=metadata.get("metrics", {}),
            tags=metadata.get("tags", []),
            embedding=embedding,
            created_at=created_at or datetime.utcnow(),
            resolved_at=resolved_at,
            meta_data=metadata.get("meta_data", {}),
        )


class KnowledgeBaseConfig(BaseModel):
    """Configuration for Incident Knowledge Base.

    Attributes:
        similarity_threshold: Minimum similarity score for matches.
        max_results: Maximum number of results to return.
        enable_embedding: Whether to use vector embeddings.
        embedding_model: Model to use for embeddings.
        use_vector_store: Whether to use embedded vector store.
        vector_store_config: Configuration for vector store.
    """

    similarity_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Similarity threshold"
    )
    max_results: int = Field(default=5, ge=1, description="Maximum results")
    enable_embedding: bool = Field(default=True, description="Enable embeddings")
    embedding_model: str = Field(
        default="text-embedding-3-small", description="Embedding model"
    )
    use_vector_store: bool = Field(
        default=True, description="Use embedded vector store (ChromaDB)"
    )
    vector_store_config: VectorStoreConfig | None = Field(
        default=None, description="Vector store configuration"
    )


class IncidentKnowledgeBase:
    """Knowledge base for storing and retrieving incidents.

    This class provides methods to store incidents with their embeddings
    and perform similarity searches to find related incidents.

    Attributes:
        config: Knowledge base configuration.
        _records: In-memory storage of incident records (fallback mode).
        _vector_store: Embedded vector store for persistence.
        _embedding_provider: Provider for generating embeddings.
    """

    def __init__(
        self,
        config: KnowledgeBaseConfig | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: EmbeddedVectorStore | None = None,
    ) -> None:
        """Initialize the knowledge base.

        Args:
            config: Knowledge base configuration. Uses defaults if None.
            embedding_provider: Provider for generating embeddings.
            vector_store: Optional vector store instance.
        """
        self.config = config or KnowledgeBaseConfig()
        self._records: dict[str, IncidentRecord] = {}
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

        # Initialize vector store if enabled and not provided
        if self.config.use_vector_store and self._vector_store is None:
            self._vector_store = EmbeddedVectorStore(
                self.config.vector_store_config or VectorStoreConfig()
            )
            self._vector_store.initialize()

    async def add_incident(
        self,
        incident: IncidentRecord,
        generate_embedding: bool = True,
    ) -> IncidentRecord:
        """Add an incident to the knowledge base.

        Args:
            incident: Incident record to add.
            generate_embedding: Whether to generate embedding.

        Returns:
            Added incident record with embedding.
        """
        # Generate embedding if needed and provider is available
        if generate_embedding and self.config.enable_embedding:
            if self._embedding_provider:
                embedding_text = incident.generate_embedding_text()
                incident.embedding = await self._embedding_provider.embed(embedding_text)
            elif not incident.embedding:
                # Generate simple hash-based embedding as fallback
                incident.embedding = self._generate_simple_embedding(incident)

        # Store in vector store if enabled
        if self.config.use_vector_store and self._vector_store is not None:
            self._vector_store.add(
                id=incident.id,
                embedding=incident.embedding or self._generate_simple_embedding(incident),
                metadata=incident.to_vector_metadata(),
                document=incident.generate_embedding_text(),
            )
        else:
            # Fallback to in-memory storage
            self._records[incident.id] = incident

        return incident

    def get_incident(self, incident_id: str) -> IncidentRecord | None:
        """Get an incident by ID.

        Args:
            incident_id: ID of the incident.

        Returns:
            Incident record if found, None otherwise.
        """
        # Try vector store first if enabled
        if self.config.use_vector_store and self._vector_store is not None:
            result = self._vector_store.get(incident_id)
            if result:
                embedding, metadata = result
                return IncidentRecord.from_vector_metadata(
                    incident_id, metadata, embedding
                )
            return None

        # Fallback to in-memory storage
        return self._records.get(incident_id)

    def update_incident(
        self,
        incident_id: str,
        **updates: Any,
    ) -> IncidentRecord | None:
        """Update an incident record.

        Args:
            incident_id: ID of the incident to update.
            **updates: Fields to update.

        Returns:
            Updated incident record if found, None otherwise.
        """
        # Get existing incident
        incident = self.get_incident(incident_id)
        if not incident:
            return None

        # Update fields
        for key, value in updates.items():
            if hasattr(incident, key):
                setattr(incident, key, value)

        # Update in vector store if enabled
        if self.config.use_vector_store and self._vector_store is not None:
            self._vector_store.update(
                id=incident_id,
                embedding=incident.embedding,
                metadata=incident.to_vector_metadata(),
                document=incident.generate_embedding_text(),
            )
        else:
            # Update in-memory storage
            self._records[incident_id] = incident

        return incident

    def delete_incident(self, incident_id: str) -> bool:
        """Delete an incident from the knowledge base.

        Args:
            incident_id: ID of the incident to delete.

        Returns:
            True if deleted, False if not found.
        """
        if self.config.use_vector_store and self._vector_store is not None:
            return self._vector_store.delete(incident_id)
        else:
            if incident_id in self._records:
                del self._records[incident_id]
                return True
            return False

    async def search_similar(
        self,
        query: str | IncidentRecord,
        top_k: int | None = None,
        threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[IncidentRecord, float]]:
        """Search for similar incidents.

        Args:
            query: Query text or incident record to search for.
            top_k: Maximum number of results. Uses config default if None.
            threshold: Minimum similarity threshold. Uses config default if None.
            filters: Optional filters to apply.

        Returns:
            List of (incident, similarity_score) tuples, sorted by similarity.
        """
        top_k = top_k or self.config.max_results
        threshold = threshold or self.config.similarity_threshold

        # Generate query embedding
        if isinstance(query, IncidentRecord):
            query_embedding = query.embedding
            if not query_embedding:
                query_embedding = self._generate_simple_embedding(query)
        else:
            if self._embedding_provider:
                query_embedding = await self._embedding_provider.embed(query)
            else:
                query_embedding = self._generate_simple_embedding_from_text(query)

        # Use vector store if enabled
        if self.config.use_vector_store and self._vector_store is not None:
            matches = self._vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                threshold=threshold,
                filters=filters,
            )

            results: list[tuple[IncidentRecord, float]] = []
            for id, similarity, metadata in matches:
                incident = IncidentRecord.from_vector_metadata(id, metadata)
                results.append((incident, similarity))

            return results

        # Fallback to in-memory search
        results = []
        for incident in self._records.values():
            # Apply filters if provided
            if filters and not self._matches_filters(incident, filters):
                continue

            # Calculate similarity
            incident_embedding = incident.embedding
            if not incident_embedding:
                incident_embedding = self._generate_simple_embedding(incident)

            similarity = self._calculate_similarity(query_embedding, incident_embedding)

            if similarity >= threshold:
                results.append((incident, similarity))

        # Sort by similarity (descending) and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def search_by_tags(
        self,
        tags: list[str],
        match_all: bool = False,
    ) -> list[IncidentRecord]:
        """Search incidents by tags.

        Args:
            tags: List of tags to search for.
            match_all: If True, all tags must match. If False, any tag matches.

        Returns:
            List of matching incidents.
        """
        results = []

        if self.config.use_vector_store and self._vector_store is not None:
            # For vector store, we need to search all and filter
            # This is a simple implementation - could be optimized with metadata filtering
            all_results = self._vector_store.search(
                query_embedding=[1.0] * 128,  # Dummy embedding to get all
                top_k=10000,
                threshold=0.0,
            )
            for id, _, metadata in all_results:
                incident_tags = metadata.get("tags", [])
                if match_all:
                    if all(tag in incident_tags for tag in tags):
                        results.append(IncidentRecord.from_vector_metadata(id, metadata))
                else:
                    if any(tag in incident_tags for tag in tags):
                        results.append(IncidentRecord.from_vector_metadata(id, metadata))
        else:
            # In-memory search
            for incident in self._records.values():
                if match_all:
                    if all(tag in incident.tags for tag in tags):
                        results.append(incident)
                else:
                    if any(tag in incident.tags for tag in tags):
                        results.append(incident)

        return results

    def search_by_service(
        self,
        service_id: str,
        anomaly_type: str | None = None,
    ) -> list[IncidentRecord]:
        """Search incidents by service.

        Args:
            service_id: Service ID to search for.
            anomaly_type: Optional anomaly type filter.

        Returns:
            List of matching incidents.
        """
        results = []

        if self.config.use_vector_store and self._vector_store is not None:
            filters = {"service_id": service_id}
            if anomaly_type:
                filters["anomaly_type"] = anomaly_type

            all_results = self._vector_store.search(
                query_embedding=[1.0] * 128,  # Dummy embedding
                top_k=10000,
                threshold=0.0,
                filters=filters,
            )
            for id, _, metadata in all_results:
                results.append(IncidentRecord.from_vector_metadata(id, metadata))
        else:
            # In-memory search
            for incident in self._records.values():
                if incident.service_id == service_id:
                    if anomaly_type is None or incident.anomaly_type == anomaly_type:
                        results.append(incident)

        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get knowledge base statistics.

        Returns:
            Dictionary with statistics.
        """
        if self.config.use_vector_store and self._vector_store is not None:
            total = self._vector_store.count()
            # For detailed stats, we'd need to scan all records
            # This is a simplified version
            return {
                "total_incidents": total,
                "by_service": {},
                "by_anomaly_type": {},
                "by_severity": {},
                "storage_type": "vector_store",
            }

        # In-memory statistics
        total = len(self._records)
        if total == 0:
            return {
                "total_incidents": 0,
                "by_service": {},
                "by_anomaly_type": {},
                "by_severity": {},
                "storage_type": "memory",
            }

        by_service: dict[str, int] = {}
        by_anomaly_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}

        for incident in self._records.values():
            by_service[incident.service_id] = by_service.get(incident.service_id, 0) + 1
            by_anomaly_type[incident.anomaly_type] = (
                by_anomaly_type.get(incident.anomaly_type, 0) + 1
            )
            by_severity[incident.severity] = by_severity.get(incident.severity, 0) + 1

        return {
            "total_incidents": total,
            "by_service": by_service,
            "by_anomaly_type": by_anomaly_type,
            "by_severity": by_severity,
            "storage_type": "memory",
        }

    def _matches_filters(
        self,
        incident: IncidentRecord,
        filters: dict[str, Any],
    ) -> bool:
        """Check if an incident matches the filters.

        Args:
            incident: Incident to check.
            filters: Filters to apply.

        Returns:
            True if incident matches all filters.
        """
        for key, value in filters.items():
            if key == "service_id" and incident.service_id != value:
                return False
            elif key == "anomaly_type" and incident.anomaly_type != value:
                return False
            elif key == "severity" and incident.severity != value:
                return False
            elif key == "status" and incident.status != value:
                return False
            elif key == "tags":
                if isinstance(value, list):
                    if not any(tag in incident.tags for tag in value):
                        return False
                elif value not in incident.tags:
                    return False
        return True

    def _calculate_similarity(
        self,
        embedding1: list[float],
        embedding2: list[float],
    ) -> float:
        """Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.

        Returns:
            Cosine similarity score (0.0 to 1.0).
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Normalize vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def _generate_simple_embedding(self, incident: IncidentRecord) -> list[float]:
        """Generate a simple hash-based embedding.

        This is a fallback when no embedding provider is available.

        Args:
            incident: Incident to generate embedding for.

        Returns:
            Simple embedding vector.
        """
        text = incident.generate_embedding_text()
        return self._generate_simple_embedding_from_text(text)

    def _generate_simple_embedding_from_text(self, text: str) -> list[float]:
        """Generate a simple hash-based embedding from text.

        Args:
            text: Text to generate embedding for.

        Returns:
            Simple embedding vector.
        """
        # Use hash to generate a deterministic vector
        hash_value = hashlib.md5(text.encode()).hexdigest()

        # Convert hash to a vector of floats
        vector_size = 128
        embedding = []
        for i in range(vector_size):
            # Use chunks of the hash to generate values
            chunk = hash_value[i % len(hash_value)]
            value = (ord(chunk) / 255.0) * 2 - 1  # Normalize to [-1, 1]
            embedding.append(value)

        return embedding

    def clear(self) -> None:
        """Clear all records from the knowledge base."""
        if self.config.use_vector_store and self._vector_store is not None:
            self._vector_store.clear()
        else:
            self._records.clear()

    def export_to_json(self) -> str:
        """Export all records to JSON.

        Returns:
            JSON string of all records.
        """
        if self.config.use_vector_store and self._vector_store is not None:
            # For vector store, we'd need to implement a scan operation
            # This is a placeholder
            return json.dumps({"note": "Export from vector store not yet implemented"})

        records = [record.to_dict() for record in self._records.values()]
        return json.dumps(records, indent=2, default=str)

    async def import_from_json(self, json_data: str) -> int:
        """Import records from JSON.

        Args:
            json_data: JSON string containing records.

        Returns:
            Number of records imported.
        """
        records = json.loads(json_data)
        count = 0
        for record_data in records:
            if isinstance(record_data, dict) and "id" in record_data:
                incident = IncidentRecord.from_dict(record_data)
                await self.add_incident(incident, generate_embedding=False)
                count += 1
        return count

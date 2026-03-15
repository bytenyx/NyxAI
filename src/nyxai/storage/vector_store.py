"""Embedded vector database storage using ChromaDB.

This module provides a local, embedded vector database for storing and searching
vector embeddings without requiring an external vector database like pgvector.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Protocol

import numpy as np
from pydantic import BaseModel, Field

from nyxai.config import get_settings


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


class VectorStoreConfig(BaseModel):
    """Configuration for vector store.

    Attributes:
        collection_name: Name of the ChromaDB collection.
        persist_directory: Directory to persist the database.
        similarity_threshold: Minimum similarity score for matches.
        max_results: Maximum number of results to return.
        embedding_dimension: Dimension of embedding vectors.
    """

    collection_name: str = Field(
        default="incidents",
        description="Name of the collection",
    )
    persist_directory: str = Field(
        default="./data/vector_db",
        description="Directory to persist the vector database",
    )
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Similarity threshold",
    )
    max_results: int = Field(
        default=5,
        ge=1,
        description="Maximum results",
    )
    embedding_dimension: int = Field(
        default=1536,
        ge=1,
        description="Embedding dimension",
    )


class EmbeddedVectorStore:
    """Embedded vector database using ChromaDB.

    This class provides methods to store and search vector embeddings locally
    without requiring an external database.

    Attributes:
        config: Vector store configuration.
        _client: ChromaDB client instance.
        _collection: ChromaDB collection instance.
    """

    def __init__(
        self,
        config: VectorStoreConfig | None = None,
    ) -> None:
        """Initialize the vector store.

        Args:
            config: Vector store configuration. Uses defaults if None.
        """
        self.config = config or VectorStoreConfig()
        self._client: Any | None = None
        self._collection: Any | None = None

    def _ensure_directory(self) -> None:
        """Ensure the persist directory exists."""
        persist_path = Path(self.config.persist_directory)
        persist_path.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        """Initialize the ChromaDB client and collection."""
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise ImportError(
                "ChromaDB is not installed. "
                "Install it with: pip install chromadb"
            )

        self._ensure_directory()

        # Create ChromaDB client with persistent storage
        self._client = chromadb.PersistentClient(
            path=self.config.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def close(self) -> None:
        """Close the vector store and release resources."""
        self._collection = None
        self._client = None

    def add(
        self,
        id: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        document: str | None = None,
    ) -> None:
        """Add a vector to the store.

        Args:
            id: Unique identifier for the vector.
            embedding: Vector embedding.
            metadata: Optional metadata dictionary.
            document: Optional document text.
        """
        if self._collection is None:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")

        # Prepare metadata (ChromaDB requires string values)
        chroma_metadata: dict[str, Any] = {}
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    chroma_metadata[key] = value
                else:
                    # Convert complex types to JSON string
                    chroma_metadata[key] = json.dumps(value)

        self._collection.add(
            ids=[id],
            embeddings=[embedding],
            metadatas=[chroma_metadata] if chroma_metadata else None,
            documents=[document] if document else None,
        )

    def add_batch(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
        documents: list[str] | None = None,
    ) -> None:
        """Add multiple vectors to the store.

        Args:
            ids: List of unique identifiers.
            embeddings: List of vector embeddings.
            metadatas: Optional list of metadata dictionaries.
            documents: Optional list of document texts.
        """
        if self._collection is None:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")

        # Prepare metadata
        chroma_metadatas: list[dict[str, Any]] | None = None
        if metadatas:
            chroma_metadatas = []
            for metadata in metadatas:
                chroma_metadata: dict[str, Any] = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        chroma_metadata[key] = value
                    else:
                        chroma_metadata[key] = json.dumps(value)
                chroma_metadatas.append(chroma_metadata)

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=chroma_metadatas,
            documents=documents,
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
        threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Search for similar vectors.

        Args:
            query_embedding: Query vector.
            top_k: Maximum number of results.
            threshold: Minimum similarity threshold.
            filters: Optional filters to apply.

        Returns:
            List of (id, similarity_score, metadata) tuples.
        """
        if self._collection is None:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")

        top_k = top_k or self.config.max_results
        threshold = threshold or self.config.similarity_threshold

        # Prepare where clause for filters
        where_clause: dict[str, Any] | None = None
        if filters:
            where_clause = {}
            for key, value in filters.items():
                if isinstance(value, (str, int, float, bool)):
                    where_clause[key] = value

        # Query the collection
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["metadatas", "distances"],
        )

        # Process results
        matches: list[tuple[str, float, dict[str, Any]]] = []
        if results["ids"] and results["ids"][0]:
            for i, id in enumerate(results["ids"][0]):
                # ChromaDB returns distance (0 = identical), convert to similarity
                distance = results["distances"][0][i]
                similarity = 1.0 - distance

                if similarity >= threshold:
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    # Parse JSON strings back to objects
                    parsed_metadata: dict[str, Any] = {}
                    for key, value in metadata.items():
                        if isinstance(value, str):
                            try:
                                parsed_metadata[key] = json.loads(value)
                            except json.JSONDecodeError:
                                parsed_metadata[key] = value
                        else:
                            parsed_metadata[key] = value

                    matches.append((id, similarity, parsed_metadata))

        return matches

    def get(self, id: str) -> tuple[list[float], dict[str, Any]] | None:
        """Get a vector by ID.

        Args:
            id: Vector ID.

        Returns:
            Tuple of (embedding, metadata) if found, None otherwise.
        """
        if self._collection is None:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")

        result = self._collection.get(
            ids=[id],
            include=["embeddings", "metadatas"],
        )

        if not result["ids"]:
            return None

        # Convert numpy array to list if necessary
        embeddings = result.get("embeddings")
        if embeddings is not None and len(embeddings) > 0:
            raw_embedding = embeddings[0]
            if hasattr(raw_embedding, 'tolist'):
                embedding = raw_embedding.tolist()
            else:
                embedding = list(raw_embedding)
        else:
            embedding = []

        metadatas = result.get("metadatas")
        metadata = metadatas[0] if metadatas is not None and len(metadatas) > 0 else {}

        # Parse JSON strings
        parsed_metadata: dict[str, Any] = {}
        for key, value in metadata.items():
            if isinstance(value, str):
                try:
                    parsed_metadata[key] = json.loads(value)
                except json.JSONDecodeError:
                    parsed_metadata[key] = value
            else:
                parsed_metadata[key] = value

        return embedding, parsed_metadata

    def delete(self, id: str) -> bool:
        """Delete a vector by ID.

        Args:
            id: Vector ID.

        Returns:
            True if deleted, False otherwise.
        """
        if self._collection is None:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")

        try:
            self._collection.delete(ids=[id])
            return True
        except Exception:
            return False

    def update(
        self,
        id: str,
        embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
        document: str | None = None,
    ) -> bool:
        """Update a vector.

        Args:
            id: Vector ID.
            embedding: New embedding (optional).
            metadata: New metadata (optional).
            document: New document text (optional).

        Returns:
            True if updated, False otherwise.
        """
        if self._collection is None:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")

        try:
            # Prepare metadata
            chroma_metadata: dict[str, Any] | None = None
            if metadata:
                chroma_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        chroma_metadata[key] = value
                    else:
                        chroma_metadata[key] = json.dumps(value)

            self._collection.update(
                ids=[id],
                embeddings=[embedding] if embedding else None,
                metadatas=[chroma_metadata] if chroma_metadata else None,
                documents=[document] if document else None,
            )
            return True
        except Exception:
            return False

    def count(self) -> int:
        """Get the number of vectors in the store.

        Returns:
            Number of vectors.
        """
        if self._collection is None:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")

        return self._collection.count()

    def clear(self) -> None:
        """Clear all vectors from the store."""
        if self._collection is None:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")

        self._client.delete_collection(self.config.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": "cosine"},
        )


# Global vector store instance
_vector_store: EmbeddedVectorStore | None = None


def get_vector_store() -> EmbeddedVectorStore:
    """Get the global vector store instance.

    Returns:
        The global vector store instance.
    """
    global _vector_store
    if _vector_store is None:
        settings = get_settings()
        vector_settings = settings.vector
        config = VectorStoreConfig(
            collection_name=vector_settings.collection_name,
            persist_directory=vector_settings.persist_directory,
            similarity_threshold=vector_settings.similarity_threshold,
            max_results=vector_settings.max_results,
        )
        _vector_store = EmbeddedVectorStore(config)
        _vector_store.initialize()
    return _vector_store


def close_vector_store() -> None:
    """Close the global vector store."""
    global _vector_store
    if _vector_store is not None:
        _vector_store.close()
        _vector_store = None

from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings


class VectorStoreService:
    def __init__(self, persist_dir: str = "./chroma_data"):
        self.client = chromadb.PersistentClient(path=persist_dir)

    async def add(
        self,
        collection: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        col = self.client.get_or_create_collection(collection)
        col.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids or [str(i) for i in range(len(documents))],
        )

    async def search(
        self,
        collection: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        col = self.client.get_or_create_collection(collection)
        results = col.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
        )
        
        return [
            {
                "id": results["ids"][0][i] if results["ids"] else None,
                "document": results["documents"][0][i] if results["documents"] else None,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else None,
                "distance": results["distances"][0][i] if results["distances"] else None,
            }
            for i in range(min(n_results, len(results["ids"][0]) if results["ids"] else 0))
        ]

    async def delete(
        self,
        collection: str,
        ids: Optional[List[str]] = None,
    ) -> None:
        col = self.client.get_or_create_collection(collection)
        if ids:
            col.delete(ids=ids)

    async def list_collections(self) -> List[str]:
        return [c.name for c in self.client.list_collections()]

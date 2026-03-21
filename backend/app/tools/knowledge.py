from typing import Any, Dict, List, Optional
import uuid

from app.services.vector_store import VectorStoreService


class KnowledgeTool:
    def __init__(self, persist_dir: str = "./chroma_data"):
        self.vector_store = VectorStoreService(persist_dir=persist_dir)

    async def add_knowledge(
        self,
        knowledge_type: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        knowledge_id = str(uuid.uuid4())
        
        await self.vector_store.add(
            collection=f"knowledge_{knowledge_type}",
            documents=[f"{title}\n{content}"],
            metadatas=[{
                "knowledge_type": knowledge_type,
                "title": title,
                **(metadata or {}),
            }],
            ids=[knowledge_id],
        )
        
        return knowledge_id

    async def search_similar(
        self,
        query: str,
        knowledge_type: Optional[str] = None,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        collection = f"knowledge_{knowledge_type}" if knowledge_type else "knowledge_all"
        
        return await self.vector_store.search(
            collection=collection,
            query=query,
            n_results=n_results,
        )

    async def search_by_type(
        self,
        query: str,
        knowledge_type: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        return await self.search_similar(
            query=query,
            knowledge_type=knowledge_type,
            n_results=n_results,
        )

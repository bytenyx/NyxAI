from typing import Any, Dict, List, Optional
import httpx


class LokiTool:
    def __init__(self, url: str):
        self.url = url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def query(
        self,
        query: str,
        limit: int = 100,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        from datetime import datetime, timedelta
        
        if not start:
            start = (datetime.now() - timedelta(hours=1)).isoformat()
        if not end:
            end = datetime.now().isoformat()
        
        response = await self.client.get(
            f"{self.url}/loki/api/v1/query_range",
            params={
                "query": query,
                "limit": limit,
                "start": start,
                "end": end,
            },
        )
        response.raise_for_status()
        return response.json().get("data", {}).get("result", [])

    async def search_logs(
        self,
        pattern: str,
        app: Optional[str] = None,
        duration_minutes: int = 30,
    ) -> List[Dict[str, Any]]:
        from datetime import datetime, timedelta
        
        query = pattern
        if app:
            query = f'{{app="{app}"}} =~ `{pattern}`'
        
        end = datetime.now()
        start = end - timedelta(minutes=duration_minutes)
        
        return await self.query(query, start=start.isoformat(), end=end.isoformat())

    async def close(self):
        await self.client.aclose()

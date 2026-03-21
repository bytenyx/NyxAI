from typing import Any, Dict, List, Optional
import httpx


class JaegerTool:
    def __init__(self, url: str):
        self.url = url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_trace(self, trace_id: str) -> Dict[str, Any]:
        response = await self.client.get(
            f"{self.url}/api/traces/{trace_id}",
        )
        response.raise_for_status()
        return response.json()

    async def search_traces(
        self,
        service: str,
        operation: Optional[str] = None,
        limit: int = 20,
        lookback: str = "1h",
    ) -> List[Dict[str, Any]]:
        params = {
            "service": service,
            "limit": limit,
            "lookback": lookback,
        }
        if operation:
            params["operation"] = operation
        
        response = await self.client.get(
            f"{self.url}/api/traces",
            params=params,
        )
        response.raise_for_status()
        return response.json().get("data", [])

    async def get_slow_traces(
        self,
        service: str,
        min_duration_ms: int = 1000,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        params = {
            "service": service,
            "limit": limit,
            "lookback": "1h",
            "minDuration": f"{min_duration_ms}ms",
        }
        
        response = await self.client.get(
            f"{self.url}/api/traces",
            params=params,
        )
        response.raise_for_status()
        return response.json().get("data", [])

    async def close(self):
        await self.client.aclose()

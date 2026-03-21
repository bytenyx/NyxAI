from typing import Any, Dict, List, Optional
import httpx


class PrometheusTool:
    def __init__(self, url: str):
        self.url = url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def query(
        self,
        query: str,
        time: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {"query": query}
        if time:
            params["time"] = time
        
        response = await self.client.get(
            f"{self.url}/api/v1/query",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def query_range(
        self,
        query: str,
        start: str,
        end: str,
        step: str = "15s",
    ) -> Dict[str, Any]:
        response = await self.client.get(
            f"{self.url}/api/v1/query_range",
            params={"query": query, "start": start, "end": end, "step": step},
        )
        response.raise_for_status()
        return response.json()

    async def get_metric_anomalies(
        self,
        query: str,
        threshold: float,
        duration_minutes: int = 5,
    ) -> List[Dict[str, Any]]:
        from datetime import datetime, timedelta
        
        end = datetime.now()
        start = end - timedelta(minutes=duration_minutes)
        
        result = await self.query_range(
            query=query,
            start=start.isoformat(),
            end=end.isoformat(),
        )
        
        anomalies = []
        for item in result.get("data", {}).get("result", []):
            for timestamp, value in item.get("values", []):
                if float(value) > threshold:
                    anomalies.append({
                        "metric": item.get("metric", {}),
                        "timestamp": timestamp,
                        "value": float(value),
                        "threshold": threshold,
                    })
        
        return anomalies

    async def close(self):
        await self.client.aclose()

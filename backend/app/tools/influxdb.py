from typing import Any, Dict, List
import httpx


class InfluxDBTool:
    def __init__(self, url: str, token: str, org: str):
        self.url = url.rstrip("/")
        self.token = token
        self.org = org
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Token {token}"},
        )

    async def query(
        self,
        query: str,
        bucket: str,
    ) -> List[Dict[str, Any]]:
        response = await self.client.post(
            f"{self.url}/api/v2/query",
            params={"org": self.org},
            headers={
                "Content-Type": "application/vnd.flux",
                "Accept": "application/json",
            },
            content=query,
        )
        response.raise_for_status()
        return self._parse_flux_response(response.text)

    def _parse_flux_response(self, text: str) -> List[Dict[str, Any]]:
        results = []
        lines = text.strip().split("\n")
        headers = None
        
        for line in lines:
            if not line:
                continue
            parts = line.split(",")
            if headers is None:
                headers = parts
            else:
                result = {}
                for i, header in enumerate(headers):
                    if i < len(parts):
                        result[header] = parts[i]
                results.append(result)
        
        return results

    async def close(self):
        await self.client.aclose()

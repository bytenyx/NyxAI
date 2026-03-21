import time
from typing import Tuple

import httpx


async def test_prometheus(url: str, timeout: int = 5) -> Tuple[bool, str, int]:
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url.rstrip('/')}/api/v1/status/config")
            latency = int((time.time() - start) * 1000)
            if response.status_code == 200:
                return True, "连接成功", latency
            return False, f"HTTP {response.status_code}", latency
    except Exception as e:
        return False, str(e), 0


async def test_loki(url: str, timeout: int = 5) -> Tuple[bool, str, int]:
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url.rstrip('/')}/ready")
            latency = int((time.time() - start) * 1000)
            if response.status_code == 200:
                return True, "连接成功", latency
            return False, f"HTTP {response.status_code}", latency
    except Exception as e:
        return False, str(e), 0


async def test_influxdb(url: str, timeout: int = 5) -> Tuple[bool, str, int]:
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url.rstrip('/')}/health")
            latency = int((time.time() - start) * 1000)
            if response.status_code == 200:
                return True, "连接成功", latency
            return False, f"HTTP {response.status_code}", latency
    except Exception as e:
        return False, str(e), 0


async def test_jaeger(url: str, timeout: int = 5) -> Tuple[bool, str, int]:
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url.rstrip('/')}/api/services")
            latency = int((time.time() - start) * 1000)
            if response.status_code == 200:
                return True, "连接成功", latency
            return False, f"HTTP {response.status_code}", latency
    except Exception as e:
        return False, str(e), 0


async def test_datasource(ds_type: str, url: str) -> Tuple[bool, str, int]:
    testers = {
        "prometheus": test_prometheus,
        "loki": test_loki,
        "influxdb": test_influxdb,
        "jaeger": test_jaeger,
    }
    tester = testers.get(ds_type)
    if tester:
        return await tester(url)
    return False, "不支持的数据源类型", 0

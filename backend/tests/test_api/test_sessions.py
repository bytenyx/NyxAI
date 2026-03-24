import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_list_sessions_without_status():
    """Test that list_sessions works without status parameter (the bug case)"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/sessions?page=1&page_size=20")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data


@pytest.mark.asyncio
async def test_list_sessions_with_status():
    """Test that list_sessions works with status parameter"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/sessions?page=1&page_size=20&status=active")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_get_session_executions():
    """Test that get_session_executions returns execution records"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/sessions/test-session-id/executions")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "data" in data
            assert isinstance(data["data"], list)

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_list_configs_empty():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/agent-configs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_and_get_config():
    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/api/v1/agent-configs", json={
            "agent_type": "diagnosis",
            "name": "测试诊断配置",
            "system_prompt": "你是一个诊断专家",
            "allowed_skills": ["brainstorming"]
        })
    assert create_response.status_code in [200, 201]
    data = create_response.json()
    assert data["data"]["agent_type"] == "diagnosis"

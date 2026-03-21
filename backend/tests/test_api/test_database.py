import pytest
from sqlalchemy import text
from app.storage.database import get_async_session, async_engine, Base


@pytest.mark.asyncio
async def test_database_connection():
    async with async_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.asyncio
async def test_get_async_session():
    async for session in get_async_session():
        assert session is not None
        break

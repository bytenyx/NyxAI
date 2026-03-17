#!/usr/bin/env python3
"""Test script to verify system initialization."""

import asyncio
from nyxai.config import get_settings
from nyxai.storage.database import init_db, close_db
from nyxai.storage.cache import init_cache, close_cache
from nyxai.storage.vector_store import get_vector_store, close_vector_store

async def test_system():
    """Test system initialization."""
    print("Testing system initialization...")
    
    # Test settings
    settings = get_settings()
    print(f"App name: {settings.app_name}")
    print(f"Database URL: {settings.db.url}")
    print(f"Vector store enabled: {settings.vector.enabled}")
    
    # Test database initialization
    print("\nInitializing database...")
    try:
        db_manager = await init_db()
        health = await db_manager.health_check()
        print(f"Database health check: {health}")
        await close_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")
    
    # Test cache initialization
    print("\nInitializing cache...")
    try:
        cache_manager = await init_cache()
        health = await cache_manager.health_check()
        print(f"Cache health check: {health}")
        await close_cache()
        print("Cache initialized successfully")
    except Exception as e:
        print(f"Cache initialization error: {e}")
    
    # Test vector store initialization
    print("\nInitializing vector store...")
    try:
        vector_store = get_vector_store()
        print(f"Vector store initialized successfully")
        close_vector_store()
    except Exception as e:
        print(f"Vector store initialization error: {e}")
    
    print("\nSystem initialization test completed!")

if __name__ == "__main__":
    asyncio.run(test_system())
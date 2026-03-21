from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.storage.database import async_engine, Base
from app.utils.logger import setup_logging
from app.api.sessions import router as sessions_router
from app.api.chat import router as chat_router
from app.api.knowledge import router as knowledge_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Agent Ops Intelligence System",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(knowledge_router)


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

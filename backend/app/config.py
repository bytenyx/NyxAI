from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "NyxAI"
    DEBUG: bool = False
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./nyxai.db"
    
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o"
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    
    PROMETHEUS_URL: Optional[str] = None
    INFLUXDB_URL: Optional[str] = None
    INFLUXDB_TOKEN: Optional[str] = None
    LOKI_URL: Optional[str] = None
    JAEGER_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()

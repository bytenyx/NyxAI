from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "NyxAI"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./nyxai.db"
    
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o"
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_MOCK_DELAY: float = 0.0
    
    SKILLS_DIR: str = "backend/skills"
    
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    
    PROMETHEUS_URL: Optional[str] = None
    INFLUXDB_URL: Optional[str] = None
    INFLUXDB_TOKEN: Optional[str] = None
    LOKI_URL: Optional[str] = None
    JAEGER_URL: Optional[str] = None
    
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"
    
    LOG_DIR: str = "./logs"
    LOG_LEVEL: str = "INFO"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_FILE_BACKUP_COUNT: int = 5
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    LOG_TO_FILE: bool = True
    LOG_TO_CONSOLE: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        if self.ENVIRONMENT == "development":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()

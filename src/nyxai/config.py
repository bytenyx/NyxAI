"""Configuration management for NyxAI.

This module provides centralized configuration management using pydantic-settings.
All settings can be loaded from environment variables with the NYX_ prefix.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    model_config = SettingsConfigDict(env_prefix="NYX_DB_")

    url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/nyxai",
        description="PostgreSQL connection URL",
    )
    echo: bool = Field(default=False, description="Enable SQL echo logging")
    pool_size: int = Field(default=10, ge=1, description="Connection pool size")
    max_overflow: int = Field(default=20, ge=0, description="Max overflow connections")
    pool_timeout: int = Field(default=30, ge=1, description="Pool timeout in seconds")


class RedisSettings(BaseSettings):
    """Redis connection settings."""

    model_config = SettingsConfigDict(env_prefix="NYX_REDIS_")

    url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    password: str | None = Field(default=None, description="Redis password")
    socket_timeout: int = Field(default=5, ge=1, description="Socket timeout in seconds")
    socket_connect_timeout: int = Field(
        default=5, ge=1, description="Socket connection timeout in seconds"
    )


class LLMSettings(BaseSettings):
    """LLM provider settings."""

    model_config = SettingsConfigDict(env_prefix="NYX_LLM_")

    provider: Literal["openai", "anthropic", "azure"] = Field(
        default="openai",
        description="LLM provider",
    )
    api_key: str | None = Field(default=None, description="API key for the LLM provider")
    model: str = Field(default="gpt-4", description="Model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int | None = Field(default=None, ge=1, description="Maximum tokens to generate")
    timeout: int = Field(default=60, ge=1, description="Request timeout in seconds")
    base_url: str | None = Field(default=None, description="Custom base URL for API")

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is within valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


class PrometheusSettings(BaseSettings):
    """Prometheus integration settings."""

    model_config = SettingsConfigDict(env_prefix="NYX_PROM_")

    url: str = Field(
        default="http://localhost:9090",
        description="Prometheus server URL",
    )
    timeout: int = Field(default=30, ge=1, description="Request timeout in seconds")
    step: str = Field(default="15s", description="Query step interval")


class CelerySettings(BaseSettings):
    """Celery task queue settings."""

    model_config = SettingsConfigDict(env_prefix="NYX_CELERY_")

    broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL",
    )
    result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL",
    )
    task_serializer: str = Field(default="json", description="Task serializer")
    accept_content: list[str] = Field(
        default_factory=lambda: ["json"],
        description="Accepted content types",
    )
    result_serializer: str = Field(default="json", description="Result serializer")
    timezone: str = Field(default="UTC", description="Timezone for Celery")
    enable_utc: bool = Field(default=True, description="Enable UTC timezone")
    task_track_started: bool = Field(default=True, description="Track task start")
    task_time_limit: int = Field(default=3600, ge=1, description="Task time limit in seconds")


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    model_config = SettingsConfigDict(env_prefix="NYX_LOG_")

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    format: Literal["json", "console"] = Field(
        default="console",
        description="Log output format",
    )
    file_path: Path | None = Field(default=None, description="Log file path")
    max_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        ge=1024,
        description="Max log file size in bytes",
    )
    backup_count: int = Field(default=5, ge=0, description="Number of backup files to keep")


class AnomalyDetectionSettings(BaseSettings):
    """Anomaly detection algorithm settings."""

    model_config = SettingsConfigDict(env_prefix="NYX_ANOMALY_")

    window_size: int = Field(default=100, ge=10, description="Detection window size")
    sensitivity: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Detection sensitivity (0-1)",
    )
    min_anomaly_duration: int = Field(
        default=3,
        ge=1,
        description="Minimum consecutive points to trigger anomaly",
    )
    algorithms: list[str] = Field(
        default_factory=lambda: ["isolation_forest", "prophet", "statistical"],
        description="Enabled detection algorithms",
    )


class Settings(BaseSettings):
    """Main application settings.

    All settings can be configured via environment variables with the NYX_ prefix.
    For nested settings, use the nested class's prefix (e.g., NYX_DB_URL).
    """

    model_config = SettingsConfigDict(
        env_prefix="NYX_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Application settings
    app_name: str = Field(default="NyxAI", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Environment",
    )

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=1, ge=1, description="Number of worker processes")

    # Security settings
    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for encryption",
    )
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed CORS hosts",
    )

    # Nested settings
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    prometheus: PrometheusSettings = Field(default_factory=PrometheusSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    anomaly: AnomalyDetectionSettings = Field(default_factory=AnomalyDetectionSettings)

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:  # noqa: ANN001
        """Warn if using default secret key in production."""
        if v == "change-me-in-production":
            values = info.data
            if values.get("env") == "production":
                raise ValueError("Secret key must be changed in production environment")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings singleton.

    Example:
        >>> from nyxai.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.app_name)
        'NyxAI'
    """
    return Settings()


# Global settings instance for convenience
settings = get_settings()

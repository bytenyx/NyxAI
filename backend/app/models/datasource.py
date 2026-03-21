from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class DataSourceBase(BaseModel):
    type: Literal["prometheus", "influxdb", "loki", "jaeger"]
    name: str
    url: str
    auth_type: Literal["none", "basic", "bearer", "api_key"] = "none"
    auth_config: Optional[dict] = None


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    auth_type: Optional[str] = None
    auth_config: Optional[dict] = None


class DataSource(DataSourceBase):
    id: str
    status: str
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DataSourceTestResult(BaseModel):
    success: bool
    message: str
    latency_ms: Optional[int] = None

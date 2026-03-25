from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AgentConfigBase(BaseModel):
    agent_type: str = Field(..., description="Agent类型")
    name: str = Field(..., description="配置名称")
    system_prompt: str = Field(..., description="系统提示词")
    allowed_skills: List[str] = Field(default_factory=list, description="可用技能列表")


class AgentConfigCreate(AgentConfigBase):
    pass


class AgentConfigUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    allowed_skills: Optional[List[str]] = None
    change_reason: Optional[str] = None


class AgentConfig(AgentConfigBase):
    id: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentConfigVersionBase(BaseModel):
    version: int
    system_prompt: str
    allowed_skills: List[str]
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None


class AgentConfigVersion(AgentConfigVersionBase):
    id: str
    config_id: str
    created_at: datetime

    class Config:
        from_attributes = True

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_config import AgentConfig, AgentConfigCreate, AgentConfigUpdate, AgentConfigVersion
from app.storage.models import AgentConfigDB, AgentConfigVersionDB
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AgentConfigRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> List[AgentConfig]:
        result = await self.session.execute(
            select(AgentConfigDB).order_by(AgentConfigDB.agent_type, AgentConfigDB.created_at.desc())
        )
        configs = result.scalars().all()
        return [self._to_model(c) for c in configs]

    async def get_by_type(self, agent_type: str) -> Optional[AgentConfig]:
        result = await self.session.execute(
            select(AgentConfigDB).where(
                and_(AgentConfigDB.agent_type == agent_type, AgentConfigDB.is_active == True)
            )
        )
        config = result.scalar_one_or_none()
        return self._to_model(config) if config else None

    async def get_by_id(self, config_id: str) -> Optional[AgentConfig]:
        result = await self.session.execute(
            select(AgentConfigDB).where(AgentConfigDB.id == config_id)
        )
        config = result.scalar_one_or_none()
        return self._to_model(config) if config else None

    async def create(self, data: AgentConfigCreate) -> AgentConfig:
        config_id = str(uuid.uuid4())
        
        db_config = AgentConfigDB(
            id=config_id,
            agent_type=data.agent_type,
            name=data.name,
            system_prompt=data.system_prompt,
            allowed_skills=data.allowed_skills,
            is_active=True,
        )
        self.session.add(db_config)
        await self.session.flush()
        
        logger.info(f"[AgentConfigRepository] Created config id={config_id} agent_type={data.agent_type}")
        return self._to_model(db_config)

    async def update(self, config_id: str, data: AgentConfigUpdate, changed_by: str = "system") -> Optional[AgentConfig]:
        result = await self.session.execute(
            select(AgentConfigDB).where(AgentConfigDB.id == config_id)
        )
        db_config = result.scalar_one_or_none()
        if not db_config:
            return None
        
        await self._create_version(db_config, changed_by, data.change_reason)
        
        if data.name is not None:
            db_config.name = data.name
        if data.system_prompt is not None:
            db_config.system_prompt = data.system_prompt
        if data.allowed_skills is not None:
            db_config.allowed_skills = data.allowed_skills
        
        db_config.updated_at = datetime.now()
        await self.session.flush()
        
        logger.info(f"[AgentConfigRepository] Updated config id={config_id}")
        return self._to_model(db_config)

    async def activate(self, config_id: str) -> Optional[AgentConfig]:
        result = await self.session.execute(
            select(AgentConfigDB).where(AgentConfigDB.id == config_id)
        )
        db_config = result.scalar_one_or_none()
        if not db_config:
            return None
        
        deactivate_result = await self.session.execute(
            select(AgentConfigDB).where(
                and_(AgentConfigDB.agent_type == db_config.agent_type, AgentConfigDB.is_active == True)
            )
        )
        for old_active in deactivate_result.scalars().all():
            old_active.is_active = False
        
        db_config.is_active = True
        await self.session.flush()
        
        logger.info(f"[AgentConfigRepository] Activated config id={config_id} agent_type={db_config.agent_type}")
        return self._to_model(db_config)

    async def delete(self, config_id: str) -> bool:
        result = await self.session.execute(
            select(AgentConfigDB).where(AgentConfigDB.id == config_id)
        )
        db_config = result.scalar_one_or_none()
        if not db_config:
            return False
        
        await self.session.delete(db_config)
        await self.session.flush()
        
        logger.info(f"[AgentConfigRepository] Deleted config id={config_id}")
        return True

    async def get_versions(self, config_id: str) -> List[AgentConfigVersion]:
        result = await self.session.execute(
            select(AgentConfigVersionDB)
            .where(AgentConfigVersionDB.config_id == config_id)
            .order_by(AgentConfigVersionDB.version.desc())
        )
        versions = result.scalars().all()
        return [self._to_version_model(v) for v in versions]

    async def rollback(self, config_id: str, version: int, changed_by: str = "system") -> Optional[AgentConfig]:
        result = await self.session.execute(
            select(AgentConfigDB).where(AgentConfigDB.id == config_id)
        )
        db_config = result.scalar_one_or_none()
        if not db_config:
            return None
        
        version_result = await self.session.execute(
            select(AgentConfigVersionDB).where(
                and_(AgentConfigVersionDB.config_id == config_id, AgentConfigVersionDB.version == version)
            )
        )
        db_version = version_result.scalar_one_or_none()
        if not db_version:
            return None
        
        await self._create_version(db_config, changed_by, f"回滚到版本 {version}")
        
        db_config.system_prompt = db_version.system_prompt
        db_config.allowed_skills = db_version.allowed_skills
        db_config.updated_at = datetime.now()
        await self.session.flush()
        
        logger.info(f"[AgentConfigRepository] Rolled back config id={config_id} to version {version}")
        return self._to_model(db_config)

    async def _create_version(self, db_config: AgentConfigDB, changed_by: str, change_reason: Optional[str]):
        version_result = await self.session.execute(
            select(AgentConfigVersionDB)
            .where(AgentConfigVersionDB.config_id == db_config.id)
            .order_by(AgentConfigVersionDB.version.desc())
            .limit(1)
        )
        last_version = version_result.scalar_one_or_none()
        next_version = (last_version.version + 1) if last_version else 1
        
        db_version = AgentConfigVersionDB(
            id=str(uuid.uuid4()),
            config_id=db_config.id,
            version=next_version,
            system_prompt=db_config.system_prompt,
            allowed_skills=db_config.allowed_skills,
            changed_by=changed_by,
            change_reason=change_reason,
        )
        self.session.add(db_version)

    def _to_model(self, db_config: Optional[AgentConfigDB]) -> Optional[AgentConfig]:
        if not db_config:
            return None
        return AgentConfig(
            id=db_config.id,
            agent_type=db_config.agent_type,
            name=db_config.name,
            system_prompt=db_config.system_prompt,
            allowed_skills=db_config.allowed_skills or [],
            is_active=db_config.is_active,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at,
        )

    def _to_version_model(self, db_version: AgentConfigVersionDB) -> AgentConfigVersion:
        return AgentConfigVersion(
            id=db_version.id,
            config_id=db_version.config_id,
            version=db_version.version,
            system_prompt=db_version.system_prompt,
            allowed_skills=db_version.allowed_skills or [],
            changed_by=db_version.changed_by,
            change_reason=db_version.change_reason,
            created_at=db_version.created_at,
        )

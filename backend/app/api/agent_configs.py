from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ApiResponse
from app.models.agent_config import (
    AgentConfig,
    AgentConfigCreate,
    AgentConfigUpdate,
    AgentConfigVersion,
)
from app.storage.database import get_async_session
from app.storage.repositories.agent_config_repo import AgentConfigRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/agent-configs", tags=["agent-configs"])


def get_skill_registry():
    from app.main import app
    return app.state.skill_registry


@router.get("", response_model=ApiResponse[List[AgentConfig]])
async def list_configs(db_session: AsyncSession = Depends(get_async_session)):
    logger.info("[API] GET /api/v1/agent-configs - Listing all configs")
    try:
        repo = AgentConfigRepository(db_session)
        configs = await repo.list_all()
        logger.info(f"[API] Retrieved {len(configs)} configs")
        return ApiResponse.success_response(data=configs)
    except Exception as e:
        logger.error(f"[API] Failed to list configs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取配置列表失败: {str(e)}")


@router.get("/skills/list")
async def list_skills():
    logger.info("[API] GET /api/v1/agent-configs/skills/list - Listing skills")
    try:
        skill_registry = get_skill_registry()
        skills = skill_registry.list_metadata()
        logger.info(f"[API] Retrieved {len(skills)} skills")
        return {"skills": skills}
    except Exception as e:
        logger.error(f"[API] Failed to list skills: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取技能列表失败: {str(e)}")


@router.get("/{agent_type}", response_model=ApiResponse[AgentConfig])
async def get_config_by_type(agent_type: str, db_session: AsyncSession = Depends(get_async_session)):
    logger.info(f"[API] GET /api/v1/agent-configs/{agent_type} - Getting config by type")
    try:
        repo = AgentConfigRepository(db_session)
        config = await repo.get_by_type(agent_type)
        if not config:
            logger.warning(f"[API] Config not found for agent_type={agent_type}")
            raise HTTPException(status_code=404, detail=f"Config not found for agent_type: {agent_type}")
        logger.info(f"[API] Config retrieved successfully agent_type={agent_type}")
        return ApiResponse.success_response(data=config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Failed to get config agent_type={agent_type}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("", response_model=ApiResponse[AgentConfig])
async def create_config(data: AgentConfigCreate, db_session: AsyncSession = Depends(get_async_session)):
    logger.info(f"[API] POST /api/v1/agent-configs - Creating config agent_type={data.agent_type}")
    try:
        repo = AgentConfigRepository(db_session)
        config = await repo.create(data)
        await db_session.commit()
        logger.info(f"[API] Config created successfully id={config.id}")
        return ApiResponse.success_response(data=config, message="配置创建成功")
    except Exception as e:
        logger.error(f"[API] Failed to create config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建配置失败: {str(e)}")


@router.put("/{config_id}", response_model=ApiResponse[AgentConfig])
async def update_config(
    config_id: str,
    data: AgentConfigUpdate,
    db_session: AsyncSession = Depends(get_async_session),
):
    logger.info(f"[API] PUT /api/v1/agent-configs/{config_id} - Updating config")
    try:
        repo = AgentConfigRepository(db_session)
        config = await repo.update(config_id, data)
        if not config:
            logger.warning(f"[API] Config not found id={config_id}")
            raise HTTPException(status_code=404, detail=f"Config not found: {config_id}")
        await db_session.commit()
        logger.info(f"[API] Config updated successfully id={config_id}")
        return ApiResponse.success_response(data=config, message="配置更新成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Failed to update config id={config_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.delete("/{config_id}", response_model=ApiResponse[None])
async def delete_config(config_id: str, db_session: AsyncSession = Depends(get_async_session)):
    logger.info(f"[API] DELETE /api/v1/agent-configs/{config_id} - Deleting config")
    try:
        repo = AgentConfigRepository(db_session)
        success = await repo.delete(config_id)
        if not success:
            logger.warning(f"[API] Config not found id={config_id}")
            raise HTTPException(status_code=404, detail=f"Config not found: {config_id}")
        await db_session.commit()
        logger.info(f"[API] Config deleted successfully id={config_id}")
        return ApiResponse.success_response(data=None, message="配置删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Failed to delete config id={config_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除配置失败: {str(e)}")


@router.post("/{config_id}/activate", response_model=ApiResponse[AgentConfig])
async def activate_config(config_id: str, db_session: AsyncSession = Depends(get_async_session)):
    logger.info(f"[API] POST /api/v1/agent-configs/{config_id}/activate - Activating config")
    try:
        repo = AgentConfigRepository(db_session)
        config = await repo.activate(config_id)
        if not config:
            logger.warning(f"[API] Config not found id={config_id}")
            raise HTTPException(status_code=404, detail=f"Config not found: {config_id}")
        await db_session.commit()
        logger.info(f"[API] Config activated successfully id={config_id}")
        return ApiResponse.success_response(data=config, message="配置激活成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Failed to activate config id={config_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"激活配置失败: {str(e)}")


@router.get("/{config_id}/versions", response_model=ApiResponse[List[AgentConfigVersion]])
async def list_versions(config_id: str, db_session: AsyncSession = Depends(get_async_session)):
    logger.info(f"[API] GET /api/v1/agent-configs/{config_id}/versions - Listing versions")
    try:
        repo = AgentConfigRepository(db_session)
        versions = await repo.get_versions(config_id)
        logger.info(f"[API] Retrieved {len(versions)} versions for config_id={config_id}")
        return ApiResponse.success_response(data=versions)
    except Exception as e:
        logger.error(f"[API] Failed to list versions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取版本历史失败: {str(e)}")


@router.post("/{config_id}/rollback/{version}", response_model=ApiResponse[AgentConfig])
async def rollback_config(
    config_id: str,
    version: int,
    db_session: AsyncSession = Depends(get_async_session),
):
    logger.info(f"[API] POST /api/v1/agent-configs/{config_id}/rollback/{version} - Rolling back")
    try:
        repo = AgentConfigRepository(db_session)
        config = await repo.rollback(config_id, version)
        if not config:
            logger.warning(f"[API] Config or version not found config_id={config_id} version={version}")
            raise HTTPException(status_code=404, detail="Config or version not found")
        await db_session.commit()
        logger.info(f"[API] Config rolled back successfully config_id={config_id} to version {version}")
        return ApiResponse.success_response(data=config, message=f"已回滚到版本 {version}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Failed to rollback config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"回滚失败: {str(e)}")

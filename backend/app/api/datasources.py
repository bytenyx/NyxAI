from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.datasource import DataSource, DataSourceCreate, DataSourceUpdate, DataSourceTestResult
from app.services.connection_tester import test_datasource
from app.storage.database import get_async_session
from app.storage.repositories.datasource_repo import DataSourceRepository

router = APIRouter(prefix="/api/v1/datasources", tags=["datasources"])


@router.get("", response_model=List[DataSource])
async def list_datasources(db_session: AsyncSession = Depends(get_async_session)):
    repo = DataSourceRepository(db_session)
    return await repo.get_all()


@router.post("", response_model=DataSource)
async def create_datasource(
    data: DataSourceCreate,
    db_session: AsyncSession = Depends(get_async_session),
):
    repo = DataSourceRepository(db_session)
    return await repo.create(data)


@router.get("/{ds_id}", response_model=DataSource)
async def get_datasource(
    ds_id: str,
    db_session: AsyncSession = Depends(get_async_session),
):
    repo = DataSourceRepository(db_session)
    ds = await repo.get_by_id(ds_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return ds


@router.put("/{ds_id}", response_model=DataSource)
async def update_datasource(
    ds_id: str,
    data: DataSourceUpdate,
    db_session: AsyncSession = Depends(get_async_session),
):
    repo = DataSourceRepository(db_session)
    ds = await repo.update(ds_id, data)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return ds


@router.delete("/{ds_id}")
async def delete_datasource(
    ds_id: str,
    db_session: AsyncSession = Depends(get_async_session),
):
    repo = DataSourceRepository(db_session)
    if not await repo.delete(ds_id):
        raise HTTPException(status_code=404, detail="数据源不存在")
    return {"message": "删除成功"}


@router.post("/{ds_id}/test", response_model=DataSourceTestResult)
async def test_datasource_connection(
    ds_id: str,
    db_session: AsyncSession = Depends(get_async_session),
):
    repo = DataSourceRepository(db_session)
    ds = await repo.get_by_id(ds_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")

    success, message, latency = await test_datasource(ds.type, ds.url)

    status = "connected" if success else "error"
    await repo.update_status(ds_id, status, None if success else message)

    return DataSourceTestResult(success=success, message=message, latency_ms=latency)

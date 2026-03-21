import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.datasource import DataSource, DataSourceCreate, DataSourceUpdate
from app.storage.models import DataSourceDB


class DataSourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> List[DataSource]:
        result = await self.session.execute(select(DataSourceDB))
        db_sources = result.scalars().all()
        return [self._to_model(ds) for ds in db_sources]

    async def get_by_id(self, ds_id: str) -> Optional[DataSource]:
        result = await self.session.execute(
            select(DataSourceDB).where(DataSourceDB.id == ds_id)
        )
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return None
        return self._to_model(db_obj)

    async def get_by_type(self, ds_type: str) -> List[DataSource]:
        result = await self.session.execute(
            select(DataSourceDB).where(DataSourceDB.type == ds_type)
        )
        db_sources = result.scalars().all()
        return [self._to_model(ds) for ds in db_sources]

    async def create(self, data: DataSourceCreate) -> DataSource:
        ds_id = str(uuid.uuid4())
        now = datetime.now()
        
        db_obj = DataSourceDB(
            id=ds_id,
            type=data.type,
            name=data.name,
            url=data.url,
            auth_type=data.auth_type,
            auth_config=data.auth_config,
            status="not_configured",
        )
        self.session.add(db_obj)
        await self.session.flush()
        
        return self._to_model(db_obj)

    async def update(self, ds_id: str, data: DataSourceUpdate) -> Optional[DataSource]:
        result = await self.session.execute(
            select(DataSourceDB).where(DataSourceDB.id == ds_id)
        )
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        
        await self.session.flush()
        return await self.get_by_id(ds_id)

    async def update_status(
        self, ds_id: str, status: str, error_message: Optional[str] = None
    ) -> Optional[DataSource]:
        result = await self.session.execute(
            select(DataSourceDB).where(DataSourceDB.id == ds_id)
        )
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return None
        
        db_obj.status = status
        db_obj.error_message = error_message
        db_obj.last_check = datetime.now()
        
        await self.session.flush()
        return await self.get_by_id(ds_id)

    async def delete(self, ds_id: str) -> bool:
        result = await self.session.execute(
            select(DataSourceDB).where(DataSourceDB.id == ds_id)
        )
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return False
        
        await self.session.delete(db_obj)
        await self.session.flush()
        return True

    def _to_model(self, db_obj: DataSourceDB) -> DataSource:
        return DataSource(
            id=db_obj.id,
            type=db_obj.type,
            name=db_obj.name,
            url=db_obj.url,
            auth_type=db_obj.auth_type,
            auth_config=db_obj.auth_config,
            status=db_obj.status,
            last_check=db_obj.last_check,
            error_message=db_obj.error_message,
            created_at=db_obj.created_at,
            updated_at=db_obj.updated_at,
        )

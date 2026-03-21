import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evidence import Evidence, EvidenceType
from app.storage.models import EvidenceDB


class EvidenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        session_id: str,
        evidence: Evidence,
    ) -> EvidenceDB:
        db_evidence = EvidenceDB(
            id=evidence.id or str(uuid.uuid4()),
            session_id=session_id,
            evidence_type=evidence.evidence_type.value,
            description=evidence.description,
            source_data=evidence.source_data,
            source_system=evidence.source_system,
            timestamp=evidence.timestamp or datetime.now(),
            confidence=evidence.confidence,
        )
        self.session.add(db_evidence)
        await self.session.flush()
        return db_evidence

    async def create_batch(
        self,
        session_id: str,
        evidence_list: List[Evidence],
    ) -> List[EvidenceDB]:
        db_evidence_list = []
        for evidence in evidence_list:
            db_evidence = await self.create(session_id, evidence)
            db_evidence_list.append(db_evidence)
        return db_evidence_list

    async def get(self, evidence_id: str) -> Optional[EvidenceDB]:
        result = await self.session.execute(
            select(EvidenceDB).where(EvidenceDB.id == evidence_id)
        )
        return result.scalar_one_or_none()

    async def get_by_session(self, session_id: str) -> List[EvidenceDB]:
        result = await self.session.execute(
            select(EvidenceDB)
            .where(EvidenceDB.session_id == session_id)
            .order_by(EvidenceDB.timestamp.asc())
        )
        return list(result.scalars().all())

    async def delete_by_session(self, session_id: str) -> int:
        result = await self.session.execute(
            select(EvidenceDB).where(EvidenceDB.session_id == session_id)
        )
        evidence_list = result.scalars().all()
        count = len(evidence_list)
        for evidence in evidence_list:
            await self.session.delete(evidence)
        await self.session.flush()
        return count

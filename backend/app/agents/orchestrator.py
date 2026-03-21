from typing import Optional

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.agents.investigation import InvestigationAgent
from app.agents.diagnosis import DiagnosisAgent
from app.agents.recovery import RecoveryAgent
from app.models.session import SessionStatus
from app.storage.repositories.session_repo import SessionRepository
from app.storage.repositories.evidence_repo import EvidenceRepository


class OrchestratorAgent(BaseAgent):
    def __init__(
        self,
        session_repo: Optional[SessionRepository] = None,
        evidence_repo: Optional[EvidenceRepository] = None,
        investigation_agent: Optional[InvestigationAgent] = None,
        diagnosis_agent: Optional[DiagnosisAgent] = None,
        recovery_agent: Optional[RecoveryAgent] = None,
    ):
        super().__init__(name="orchestrator")
        self.session_repo = session_repo
        self.evidence_repo = evidence_repo
        self.investigation = investigation_agent or InvestigationAgent()
        self.diagnosis = diagnosis_agent or DiagnosisAgent()
        self.recovery = recovery_agent or RecoveryAgent()

    async def execute(self, context: AgentContext) -> AgentResult:
        all_evidence = []
        session_id = context.session_id
        
        inv_result = await self.investigation.execute(context)
        if not inv_result.success:
            await self._update_status(session_id, SessionStatus.FAILED)
            return AgentResult(
                success=False,
                error="Investigation failed",
                data={"status": "failed", "stage": "investigation"},
            )
        all_evidence.extend(inv_result.evidence)
        
        await self._persist_evidence(session_id, inv_result.evidence)
        
        await self._update_session(
            session_id,
            status=SessionStatus.DIAGNOSING,
            investigation=inv_result.data,
        )
        
        diagnosis_context = AgentContext(
            session_id=context.session_id,
            query=context.query,
            metadata={
                "investigation_summary": inv_result.data.get("summary", ""),
                "anomalies": inv_result.data.get("anomalies", []),
                "confidence": inv_result.data.get("confidence", 0.7),
            },
        )
        diag_result = await self.diagnosis.execute(diagnosis_context)
        if not diag_result.success:
            await self._update_status(session_id, SessionStatus.FAILED)
            return AgentResult(
                success=False,
                error="Diagnosis failed",
                data={"status": "failed", "stage": "diagnosis"},
            )
        all_evidence.extend(diag_result.evidence)
        
        await self._persist_evidence(session_id, diag_result.evidence)
        
        await self._update_session(
            session_id,
            status=SessionStatus.RECOVERING,
            root_cause=diag_result.data,
        )
        
        recovery_context = AgentContext(
            session_id=context.session_id,
            query=context.query,
            metadata={
                "root_cause": diag_result.data.get("root_cause", ""),
                "confidence": diag_result.data.get("confidence", 0),
                "evidence_chain": diag_result.data.get("evidence_chain", []),
            },
        )
        rec_result = await self.recovery.execute(recovery_context)
        all_evidence.extend(rec_result.evidence)
        
        await self._persist_evidence(session_id, rec_result.evidence)
        
        await self._update_session(
            session_id,
            status=SessionStatus.COMPLETED,
            recovery_plan=rec_result.data,
        )
        
        return AgentResult(
            success=True,
            data={
                "status": "completed",
                "investigation": inv_result.data,
                "diagnosis": diag_result.data,
                "recovery": rec_result.data,
            },
            evidence=all_evidence,
        )

    async def _update_status(self, session_id: str, status: SessionStatus):
        if self.session_repo:
            await self.session_repo.update_status(session_id, status)

    async def _update_session(
        self,
        session_id: str,
        status: Optional[SessionStatus] = None,
        investigation: Optional[dict] = None,
        root_cause: Optional[dict] = None,
        recovery_plan: Optional[dict] = None,
    ):
        if self.session_repo:
            await self.session_repo.update_session(
                session_id,
                status=status,
                investigation=investigation,
                root_cause=root_cause,
                recovery_plan=recovery_plan,
            )

    async def _persist_evidence(self, session_id: str, evidence_list: list):
        if self.evidence_repo and evidence_list:
            await self.evidence_repo.create_batch(session_id, evidence_list)

from typing import Any, AsyncGenerator, Dict, Optional
import uuid

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

    async def run_stream(
        self, session_id: str, content: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        agent_identity = {
            "id": str(uuid.uuid4()),
            "name": "OrchestratorAgent",
            "display_name": "编排Agent",
            "type": "orchestrator",
        }

        yield {
            "type": "orchestrator_status",
            "payload": {
                "status": "started",
                "plan": ["InvestigationAgent", "DiagnosisAgent", "RecoveryAgent"],
            },
            "agent": agent_identity,
        }

        context = AgentContext(session_id=session_id, query=content, metadata={})

        investigation_identity = {
            "id": f"investigation_{uuid.uuid4().hex[:8]}",
            "name": "InvestigationAgent",
            "display_name": "调查Agent",
            "type": "investigation",
            "icon": "search",
        }

        yield {
            "type": "agent_start",
            "agent": investigation_identity,
            "payload": {"description": "开始调查异常..."},
        }

        yield {
            "type": "agent_thinking",
            "agent": investigation_identity,
            "payload": {"thought": f"分析用户输入: {content}"},
        }

        inv_result = await self.investigation.execute(context)

        if inv_result.evidence:
            for ev in inv_result.evidence:
                source = getattr(ev, "source_system", "unknown")
                source_data = getattr(ev, "source_data", {})
                yield {
                    "type": "tool_call",
                    "agent": investigation_identity,
                    "payload": {"tool": source, "params": {}},
                }
                yield {
                    "type": "tool_result",
                    "agent": investigation_identity,
                    "payload": {"tool": source, "result": source_data},
                }

        yield {
            "type": "agent_complete",
            "agent": investigation_identity,
            "payload": {"summary": inv_result.data.get("summary", "调查完成")},
        }

        if not inv_result.success:
            yield {
                "type": "error",
                "payload": {"message": "Investigation failed", "stage": "investigation"},
            }
            return

        diagnosis_identity = {
            "id": f"diagnosis_{uuid.uuid4().hex[:8]}",
            "name": "DiagnosisAgent",
            "display_name": "诊断Agent",
            "type": "diagnosis",
            "icon": "diagnosis",
        }

        yield {
            "type": "handoff",
            "agent": investigation_identity,
            "payload": {
                "to_agent": diagnosis_identity,
                "context": "调查完成，进入根因分析阶段",
            },
        }

        yield {
            "type": "agent_start",
            "agent": diagnosis_identity,
            "payload": {"description": "开始根因分析..."},
        }

        diagnosis_context = AgentContext(
            session_id=context.session_id,
            query=context.query,
            metadata={
                "investigation_summary": inv_result.data.get("summary", ""),
                "anomalies": inv_result.data.get("anomalies", []),
            },
        )
        diag_result = await self.diagnosis.execute(diagnosis_context)

        yield {
            "type": "agent_thinking",
            "agent": diagnosis_identity,
            "payload": {"thought": "分析因果关系..."},
        }

        yield {
            "type": "agent_complete",
            "agent": diagnosis_identity,
            "payload": {"summary": diag_result.data.get("root_cause", "诊断完成")},
        }

        if not diag_result.success:
            yield {
                "type": "error",
                "payload": {"message": "Diagnosis failed", "stage": "diagnosis"},
            }
            return

        recovery_identity = {
            "id": f"recovery_{uuid.uuid4().hex[:8]}",
            "name": "RecoveryAgent",
            "display_name": "恢复Agent",
            "type": "recovery",
            "icon": "recovery",
        }

        yield {
            "type": "handoff",
            "agent": diagnosis_identity,
            "payload": {
                "to_agent": recovery_identity,
                "context": "诊断完成，生成恢复方案",
            },
        }

        yield {
            "type": "agent_start",
            "agent": recovery_identity,
            "payload": {"description": "生成恢复方案..."},
        }

        recovery_context = AgentContext(
            session_id=context.session_id,
            query=context.query,
            metadata={
                "root_cause": diag_result.data.get("root_cause", ""),
                "evidence_chain": diag_result.data.get("evidence_chain", []),
            },
        )
        rec_result = await self.recovery.execute(recovery_context)

        yield {
            "type": "agent_complete",
            "agent": recovery_identity,
            "payload": {"summary": rec_result.data.get("plan", "恢复方案已生成")},
        }

        yield {
            "type": "session_complete",
            "payload": {
                "status": "success",
                "summary": "根因已定位，恢复方案已生成",
                "agents_involved": [
                    "InvestigationAgent",
                    "DiagnosisAgent",
                    "RecoveryAgent",
                ],
            },
        }

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

from typing import Any, AsyncGenerator, Dict, Optional
import uuid
from datetime import datetime

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.agents.investigation import InvestigationAgent
from app.agents.diagnosis import DiagnosisAgent
from app.agents.recovery import RecoveryAgent
from app.models.session import SessionStatus
from app.models.agent import AgentExecutionCreate, AgentIdentity
from app.storage.repositories.session_repo import SessionRepository
from app.storage.repositories.evidence_repo import EvidenceRepository
from app.storage.repositories.agent_exec_repo import AgentExecutionRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OrchestratorAgent(BaseAgent):
    def __init__(
        self,
        session_repo: Optional[SessionRepository] = None,
        evidence_repo: Optional[EvidenceRepository] = None,
        agent_exec_repo: Optional[AgentExecutionRepository] = None,
        investigation_agent: Optional[InvestigationAgent] = None,
        diagnosis_agent: Optional[DiagnosisAgent] = None,
        recovery_agent: Optional[RecoveryAgent] = None,
    ):
        super().__init__(name="orchestrator")
        self.session_repo = session_repo
        self.evidence_repo = evidence_repo
        self.agent_exec_repo = agent_exec_repo
        self.investigation = investigation_agent or InvestigationAgent()
        self.diagnosis = diagnosis_agent or DiagnosisAgent()
        self.recovery = recovery_agent or RecoveryAgent()

    async def execute(self, context: AgentContext) -> AgentResult:
        all_evidence = []
        session_id = context.session_id
        start_time = time.time()
        
        logger.info("=" * 80)
        logger.info(f"[Orchestrator] Starting execution for session_id={session_id}")
        logger.info(f"[Orchestrator] Query: {context.query[:200]}{'...' if len(context.query) > 200 else ''}")
        
        inv_start = time.time()
        logger.info(f"[Orchestrator] Starting InvestigationAgent")
        inv_result = await self.investigation.execute(context)
        inv_duration = time.time() - inv_start
        
        if not inv_result.success:
            logger.error(f"[Orchestrator] Investigation failed for session_id={session_id} after {inv_duration:.2f}s")
            await self._update_status(session_id, SessionStatus.FAILED)
            return AgentResult(
                success=False,
                error="Investigation failed",
                data={"status": "failed", "stage": "investigation"},
            )
        
        logger.info(f"[Orchestrator] Investigation completed in {inv_duration:.2f}s, found {len(inv_result.evidence)} evidence items")
        all_evidence.extend(inv_result.evidence)
        
        await self._persist_evidence(session_id, inv_result.evidence)
        
        await self._update_session(
            session_id,
            status=SessionStatus.DIAGNOSING,
            investigation=inv_result.data,
        )
        
        diag_start = time.time()
        logger.info(f"[Orchestrator] Starting DiagnosisAgent")
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
        diag_duration = time.time() - diag_start
        
        if not diag_result.success:
            logger.error(f"[Orchestrator] Diagnosis failed for session_id={session_id} after {diag_duration:.2f}s")
            await self._update_status(session_id, SessionStatus.FAILED)
            return AgentResult(
                success=False,
                error="Diagnosis failed",
                data={"status": "failed", "stage": "diagnosis"},
            )
        
        logger.info(f"[Orchestrator] Diagnosis completed in {diag_duration:.2f}s, found {len(diag_result.evidence)} evidence items")
        all_evidence.extend(diag_result.evidence)
        
        await self._persist_evidence(session_id, diag_result.evidence)
        
        await self._update_session(
            session_id,
            status=SessionStatus.RECOVERING,
            root_cause=diag_result.data,
        )
        
        rec_start = time.time()
        logger.info(f"[Orchestrator] Starting RecoveryAgent")
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
        rec_duration = time.time() - rec_start
        
        logger.info(f"[Orchestrator] Recovery completed in {rec_duration:.2f}s, found {len(rec_result.evidence)} evidence items")
        all_evidence.extend(rec_result.evidence)
        
        await self._persist_evidence(session_id, rec_result.evidence)
        
        await self._update_session(
            session_id,
            status=SessionStatus.COMPLETED,
            recovery_plan=rec_result.data,
        )
        
        total_duration = time.time() - start_time
        logger.info(f"[Orchestrator] Execution completed successfully for session_id={session_id}")
        logger.info(f"[Orchestrator] Total duration: {total_duration:.2f}s")
        logger.info(f"[Orchestrator] Total evidence collected: {len(all_evidence)}")
        logger.info("=" * 80)
        
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

        investigation_identity = AgentIdentity(
            id=f"investigation_{uuid.uuid4().hex[:8]}",
            name="InvestigationAgent",
            display_name="调查Agent",
            type="investigation",
            icon="search",
        )

        inv_exec = await self._create_execution(session_id, investigation_identity)

        yield {
            "type": "agent_start",
            "agent": investigation_identity.model_dump(),
            "payload": {"description": "开始调查异常..."},
        }

        thought = f"分析用户输入: {content}"
        await self._add_thought(inv_exec.id, thought)
        yield {
            "type": "agent_thinking",
            "agent": investigation_identity.model_dump(),
            "payload": {"thought": thought},
        }

        inv_result = await self.investigation.execute(context)

        if inv_result.evidence:
            for ev in inv_result.evidence:
                source = getattr(ev, "source_system", "unknown")
                source_data = getattr(ev, "source_data", {})
                tool_call = {"tool": source, "params": {}, "result": source_data, "status": "success", "timestamp": datetime.utcnow().isoformat()}
                await self._add_tool_call(inv_exec.id, tool_call)
                yield {
                    "type": "tool_call",
                    "agent": investigation_identity.model_dump(),
                    "payload": {"tool": source, "params": {}},
                }
                yield {
                    "type": "tool_result",
                    "agent": investigation_identity.model_dump(),
                    "payload": {"tool": source, "result": source_data},
                }

        inv_summary = inv_result.data.get("summary", "调查完成")
        await self._complete_execution(inv_exec.id, inv_summary, inv_result.success)
        yield {
            "type": "agent_complete",
            "agent": investigation_identity.model_dump(),
            "payload": {"summary": inv_summary},
        }

        if not inv_result.success:
            yield {
                "type": "error",
                "payload": {"message": "Investigation failed", "stage": "investigation"},
            }
            return

        diagnosis_identity = AgentIdentity(
            id=f"diagnosis_{uuid.uuid4().hex[:8]}",
            name="DiagnosisAgent",
            display_name="诊断Agent",
            type="diagnosis",
            icon="diagnosis",
        )

        yield {
            "type": "handoff",
            "agent": investigation_identity.model_dump(),
            "payload": {
                "to_agent": diagnosis_identity.model_dump(),
                "context": "调查完成，进入根因分析阶段",
            },
        }

        diag_exec = await self._create_execution(session_id, diagnosis_identity)

        yield {
            "type": "agent_start",
            "agent": diagnosis_identity.model_dump(),
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

        diag_thought = "分析因果关系..."
        await self._add_thought(diag_exec.id, diag_thought)
        yield {
            "type": "agent_thinking",
            "agent": diagnosis_identity.model_dump(),
            "payload": {"thought": diag_thought},
        }

        diag_summary = diag_result.data.get("root_cause", "诊断完成")
        await self._complete_execution(diag_exec.id, diag_summary, diag_result.success)
        yield {
            "type": "agent_complete",
            "agent": diagnosis_identity.model_dump(),
            "payload": {"summary": diag_summary},
        }

        if not diag_result.success:
            yield {
                "type": "error",
                "payload": {"message": "Diagnosis failed", "stage": "diagnosis"},
            }
            return

        recovery_identity = AgentIdentity(
            id=f"recovery_{uuid.uuid4().hex[:8]}",
            name="RecoveryAgent",
            display_name="恢复Agent",
            type="recovery",
            icon="recovery",
        )

        yield {
            "type": "handoff",
            "agent": diagnosis_identity.model_dump(),
            "payload": {
                "to_agent": recovery_identity.model_dump(),
                "context": "诊断完成，生成恢复方案",
            },
        }

        rec_exec = await self._create_execution(session_id, recovery_identity)

        recovery_context = AgentContext(
            session_id=context.session_id,
            query=context.query,
            metadata={
                "root_cause": diag_result.data.get("root_cause", ""),
                "evidence_chain": diag_result.data.get("evidence_chain", []),
            },
        )
        rec_result = await self.recovery.execute(recovery_context)

        rec_summary = rec_result.data.get("plan", "恢复方案已生成")
        await self._complete_execution(rec_exec.id, rec_summary, rec_result.success)
        yield {
            "type": "agent_complete",
            "agent": recovery_identity.model_dump(),
            "payload": {"summary": rec_summary},
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

    async def _create_execution(self, session_id: str, agent: AgentIdentity):
        if self.agent_exec_repo:
            return await self.agent_exec_repo.create(
                AgentExecutionCreate(
                    session_id=session_id,
                    agent=agent,
                    status="running",
                )
            )
        return None

    async def _add_thought(self, exec_id: str, thought: str):
        if self.agent_exec_repo and exec_id:
            await self.agent_exec_repo.add_thought(exec_id, thought)

    async def _add_tool_call(self, exec_id: str, tool_call: dict):
        if self.agent_exec_repo and exec_id:
            await self.agent_exec_repo.add_tool_call(exec_id, tool_call)

    async def _complete_execution(self, exec_id: str, result: str, success: bool = True):
        if self.agent_exec_repo and exec_id:
            await self.agent_exec_repo.complete(
                exec_id,
                result,
                status="completed" if success else "failed"
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

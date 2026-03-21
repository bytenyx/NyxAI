from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.agents.investigation import InvestigationAgent
from app.agents.diagnosis import DiagnosisAgent
from app.agents.recovery import RecoveryAgent


class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="orchestrator")
        self.investigation = InvestigationAgent()
        self.diagnosis = DiagnosisAgent()
        self.recovery = RecoveryAgent()

    async def execute(self, context: AgentContext) -> AgentResult:
        all_evidence = []
        
        inv_result = await self.investigation.execute(context)
        if not inv_result.success:
            return AgentResult(
                success=False,
                error="Investigation failed",
                data={"status": "failed", "stage": "investigation"},
            )
        all_evidence.extend(inv_result.evidence)
        
        diagnosis_context = AgentContext(
            session_id=context.session_id,
            query=context.query,
            metadata={
                "investigation_summary": inv_result.data.get("summary", ""),
                "anomalies": inv_result.data.get("anomalies", []),
            },
        )
        diag_result = await self.diagnosis.execute(diagnosis_context)
        if not diag_result.success:
            return AgentResult(
                success=False,
                error="Diagnosis failed",
                data={"status": "failed", "stage": "diagnosis"},
            )
        all_evidence.extend(diag_result.evidence)
        
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

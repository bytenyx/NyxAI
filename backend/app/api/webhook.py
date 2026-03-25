from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext
from app.agents.orchestrator import OrchestratorAgent
from app.models.session import SessionStatus
from app.storage.database import get_async_session
from app.storage.repositories.session_repo import SessionRepository
from app.storage.repositories.evidence_repo import EvidenceRepository
from app.storage.repositories.agent_exec_repo import AgentExecutionRepository

router = APIRouter(prefix="/webhook", tags=["webhook"])


class AlertLabel(BaseModel):
    alertname: str = Field(..., description="告警名称")
    service: Optional[str] = None
    severity: Optional[str] = None
    instance: Optional[str] = None
    job: Optional[str] = None


class AlertAnnotation(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None


class Alert(BaseModel):
    status: str = Field(..., description="firing或resolved")
    labels: AlertLabel
    annotations: AlertAnnotation = AlertAnnotation()
    starts_at: Optional[str] = Field(None, alias="startsAt")
    ends_at: Optional[str] = Field(None, alias="endsAt")
    fingerprint: Optional[str] = None


class AlertWebhookRequest(BaseModel):
    receiver: Optional[str] = None
    status: str = "firing"
    alerts: List[Alert] = Field(default_factory=list)
    group_labels: Optional[Dict[str, str]] = Field(None, alias="groupLabels")
    common_labels: Optional[Dict[str, str]] = Field(None, alias="commonLabels")
    common_annotations: Optional[Dict[str, str]] = Field(None, alias="commonAnnotations")
    external_url: Optional[str] = Field(None, alias="externalURL")


class WebhookResponse(BaseModel):
    session_id: str
    status: str
    message: str


async def process_alert(
    session_id: str,
    alert: Alert,
    session_repo: SessionRepository,
    evidence_repo: EvidenceRepository,
    agent_exec_repo: AgentExecutionRepository,
):
    query_parts = [
        f"告警名称: {alert.labels.alertname}",
    ]
    
    if alert.labels.service:
        query_parts.append(f"服务: {alert.labels.service}")
    if alert.labels.instance:
        query_parts.append(f"实例: {alert.labels.instance}")
    if alert.labels.severity:
        query_parts.append(f"严重程度: {alert.labels.severity}")
    if alert.annotations.summary:
        query_parts.append(f"摘要: {alert.annotations.summary}")
    if alert.annotations.description:
        query_parts.append(f"详情: {alert.annotations.description}")
    
    query = "\n".join(query_parts)
    
    orchestrator = OrchestratorAgent(
        session_repo=session_repo,
        evidence_repo=evidence_repo,
        agent_exec_repo=agent_exec_repo,
    )
    context = AgentContext(
        session_id=session_id,
        query=query,
        metadata={
            "alert_status": alert.status,
            "alert_name": alert.labels.alertname,
            "trigger_type": "webhook",
        },
    )
    
    await orchestrator.execute(context)


@router.post("/alert", response_model=WebhookResponse)
async def receive_alert(
    request: AlertWebhookRequest,
    background_tasks: BackgroundTasks,
    db_session: AsyncSession = Depends(get_async_session),
):
    session_repo = SessionRepository(db_session)
    evidence_repo = EvidenceRepository(db_session)
    agent_exec_repo = AgentExecutionRepository(db_session)
    
    firing_alerts = [a for a in request.alerts if a.status == "firing"]
    
    if not firing_alerts:
        return WebhookResponse(
            session_id="",
            status="ignored",
            message="No firing alerts to process",
        )
    
    alert = firing_alerts[0]
    
    session = await session_repo.create(
        trigger_type="webhook",
        trigger_source=f"prometheus:{alert.labels.alertname}",
        status=SessionStatus.INVESTIGATING,
        title=f"Alert: {alert.labels.alertname}",
    )
    
    background_tasks.add_task(
        process_alert,
        session.id,
        alert,
        session_repo,
        evidence_repo,
        agent_exec_repo,
    )
    
    return WebhookResponse(
        session_id=session.id,
        status="processing",
        message=f"Alert '{alert.labels.alertname}' is being processed",
    )


@router.post("/custom", response_model=WebhookResponse)
async def receive_custom_webhook(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db_session: AsyncSession = Depends(get_async_session),
):
    session_repo = SessionRepository(db_session)
    evidence_repo = EvidenceRepository(db_session)
    agent_exec_repo = AgentExecutionRepository(db_session)
    
    event_type = request.get("event_type", "unknown")
    event_source = request.get("source", "custom")
    
    session = await session_repo.create(
        trigger_type="webhook",
        trigger_source=f"custom:{event_source}:{event_type}",
        status=SessionStatus.INVESTIGATING,
        title=f"Webhook: {event_type}",
    )
    
    query = request.get("message") or request.get("description") or str(request)
    
    async def process_custom():
        orchestrator = OrchestratorAgent(
            session_repo=session_repo,
            evidence_repo=evidence_repo,
            agent_exec_repo=agent_exec_repo,
        )
        context = AgentContext(
            session_id=session.id,
            query=query,
            metadata={
                "trigger_type": "webhook",
                "event_type": event_type,
                "raw_request": request,
            },
        )
        await orchestrator.execute(context)
    
    background_tasks.add_task(process_custom)
    
    return WebhookResponse(
        session_id=session.id,
        status="processing",
        message=f"Custom webhook event '{event_type}' is being processed",
    )

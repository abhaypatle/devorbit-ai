from typing import NotRequired, TypedDict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApprovalAction, AgentRun
from app.rag.retriever import Citation


class AgentState(TypedDict):
    session: AsyncSession
    run: AgentRun
    org_id: UUID
    project_id: UUID
    mode: str
    input_text: str
    action: ApprovalAction | None
    status: str
    sanitized_input: str
    context: str
    citations: list[Citation]
    scope_decision: NotRequired[str]
    risk_score: NotRequired[int]
    approval_id: NotRequired[str]
    output_text: NotRequired[str]
    generated_srs: NotRequired[str]
    milestones: NotRequired[list[dict[str, str]]]

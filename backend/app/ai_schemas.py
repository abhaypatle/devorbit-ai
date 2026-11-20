from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import ApprovalAction


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CitationRead(BaseModel):
    doc_id: UUID
    doc_title: str
    chunk_index: int
    snippet: str
    section: str | None = None
    score: float


class DocumentRead(APIModel):
    id: UUID
    org_id: UUID
    project_id: UUID
    title: str
    filename: str
    content_type: str
    storage_key: str
    is_approved: bool
    status: str
    created_at: datetime
    download_reference: str


class RAGQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=20_000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class RAGQueryResponse(BaseModel):
    status: Literal["COMPLETED", "BLOCKED"]
    answer: str
    citations: list[CitationRead]


class AgentRunRequest(BaseModel):
    mode: Literal["srs", "scope"] = "scope"
    input_text: str = Field(min_length=1, max_length=20_000)
    action: ApprovalAction | None = None


class MilestoneRead(BaseModel):
    name: str
    sequence: str


class AgentRunRead(BaseModel):
    id: UUID
    org_id: UUID
    project_id: UUID
    status: str
    mode: str
    scope_decision: str | None
    risk_score: int | None
    generated_srs: str | None
    milestones: list[MilestoneRead] | None
    output_text: str | None
    citations: list[dict[str, object]]
    input_tokens: int
    output_tokens: int
    latency_ms: int
    approval_id: UUID | None
    created_at: datetime


class ApprovalRead(APIModel):
    id: UUID
    org_id: UUID
    project_id: UUID
    agent_run_id: UUID | None
    action: str
    status: str
    idempotency_key: str
    reviewer_notes: str | None
    resolved_at: datetime | None
    action_payload: dict[str, object]
    created_at: datetime


class ApprovalResolveRequest(BaseModel):
    decision: Literal["APPROVED", "REJECTED"]
    reviewer_notes: str | None = Field(default=None, max_length=5000)

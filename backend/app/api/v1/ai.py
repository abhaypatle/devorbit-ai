from time import perf_counter
from typing import Annotated
from urllib.parse import quote
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Response, UploadFile, status
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.workflow import run_agent_workflow
from app.ai_schemas import (
    AgentRunRead,
    AgentRunRequest,
    ApprovalRead,
    ApprovalResolveRequest,
    CitationRead,
    DocumentRead,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.core.config import get_settings
from app.core.dependencies import DbSession, get_current_user, require_roles
from app.core.guardrails import GuardrailDecision, scan_egress, scan_ingress
from app.db.models import (
    ApprovalAction,
    ApprovalRequest,
    ApprovalStatus,
    AgentRun,
    AgentRunStatus,
    Client,
    DocumentStatus,
    Invoice,
    InvoiceStatus,
    LLMTaskType,
    ProjectDocument,
    ProjectOrder,
    User,
    UserRole,
)
from app.rag.chunker import chunk_document
from app.rag.embedder import get_embedder
from app.rag.parser import parse_document
from app.rag.pgvector_store import store_chunks
from app.rag.retriever import retrieve
from app.services.s3_storage import storage
from app.services.llm_telemetry import record_llm_usage

router = APIRouter(tags=["documents", "rag", "agent", "approvals"])
staff_roles = (UserRole.ADMIN, UserRole.ENGINEER)


@router.post(
    "/projects/{order_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_document(
    order_id: UUID,
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form(max_length=240)] = None,
    approved: Annotated[bool, Form()] = False,
) -> DocumentRead:
    project = await _get_project(order_id, session, user)
    if approved and user.role == UserRole.CLIENT:
        raise HTTPException(status_code=403, detail="Only staff can mark a document as approved")
    max_bytes = get_settings().max_document_bytes
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Document exceeds {max_bytes} bytes")
    filename = file.filename or "document.txt"
    try:
        parsed = parse_document(content, filename, file.content_type or "application/octet-stream")
        document_id = uuid4()
        chunks = chunk_document(
            parsed,
            org_id=user.org_id,
            project_id=project.id,
            doc_id=document_id,
        )
        embeddings = await get_embedder().embed([chunk.content for chunk in chunks])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    clean_filename = filename.replace("\\", "/").rsplit("/", 1)[-1][:255]
    content_type = file.content_type or "text/plain"
    key = storage.build_key(str(user.org_id), str(project.id), str(document_id), clean_filename)
    await storage.upload(key, content, content_type=content_type)
    document = ProjectDocument(
        id=document_id,
        org_id=user.org_id,
        project_id=project.id,
        uploaded_by_id=user.id,
        title=(title or parsed.title)[:240],
        filename=clean_filename,
        content_type=content_type[:160],
        storage_key=key,
        is_approved=approved,
        status=DocumentStatus.INDEXED,
    )
    session.add(document)
    await store_chunks(session, chunks, embeddings)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        await storage.delete(key)
        raise HTTPException(status_code=409, detail="Document could not be indexed") from None
    await session.refresh(document)
    return DocumentRead.model_validate(
        {
            **{
                field: getattr(document, field)
                for field in (
                    "id",
                    "org_id",
                    "project_id",
                    "title",
                    "filename",
                    "content_type",
                    "storage_key",
                    "is_approved",
                    "created_at",
                )
            },
            "status": document.status.value,
            "download_reference": (
                await storage.download_reference(key)
                if get_settings().storage_mode == "s3"
                else f"{get_settings().api_v1_prefix}/projects/{project.id}/documents/{document.id}/download"
            ),
        }
    )


@router.get(
    "/projects/{order_id}/documents",
    response_model=list[DocumentRead],
)
async def list_project_documents(
    order_id: UUID,
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> list[DocumentRead]:
    project = await _get_project(order_id, session, user)
    documents = await session.scalars(
        select(ProjectDocument)
        .where(
            ProjectDocument.org_id == user.org_id,
            ProjectDocument.project_id == project.id,
            ProjectDocument.status == DocumentStatus.INDEXED,
        )
        .order_by(ProjectDocument.created_at.desc())
    )
    settings = get_settings()
    result: list[DocumentRead] = []
    for document in documents:
        reference = (
            await storage.download_reference(document.storage_key)
            if settings.storage_mode == "s3"
            else f"{settings.api_v1_prefix}/projects/{project.id}/documents/{document.id}/download"
        )
        result.append(
            DocumentRead(
                id=document.id,
                org_id=document.org_id,
                project_id=document.project_id,
                title=document.title,
                filename=document.filename,
                content_type=document.content_type,
                storage_key=document.storage_key,
                is_approved=document.is_approved,
                status=document.status.value,
                created_at=document.created_at,
                download_reference=reference,
            )
        )
    return result


@router.get("/projects/{order_id}/documents/{document_id}/download")
async def download_document(
    order_id: UUID,
    document_id: UUID,
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> Response:
    project = await _get_project(order_id, session, user)
    document = await session.scalar(
        select(ProjectDocument).where(
            ProjectDocument.id == document_id,
            ProjectDocument.org_id == user.org_id,
            ProjectDocument.project_id == project.id,
            ProjectDocument.status == DocumentStatus.INDEXED,
        )
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Project document not found")
    if get_settings().storage_mode == "s3":
        return RedirectResponse(await storage.download_reference(document.storage_key), status_code=307)
    content = await storage.read(document.storage_key)
    return StreamingResponse(
        iter([content]),
        media_type=document.content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(document.filename)}"
        },
    )


@router.post("/projects/{order_id}/rag/query", response_model=RAGQueryResponse)
async def query_project_documents(
    order_id: UUID,
    payload: RAGQueryRequest,
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> RAGQueryResponse:
    project = await _get_project(order_id, session, user)
    ingress = scan_ingress(payload.query)
    if ingress.decision == GuardrailDecision.BLOCK:
        raise HTTPException(status_code=422, detail={"guardrail": "blocked", "reasons": ingress.reasons})
    try:
        result = await retrieve(
            session,
            org_id=user.org_id,
            project_id=project.id,
            query=ingress.text,
            top_k=payload.top_k,
            approved_only=False,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    safe_citations = [
        {
            **citation.as_dict(),
            "doc_title": scan_egress(citation.doc_title).text,
            "snippet": scan_egress(citation.snippet).text,
            "section": scan_egress(citation.section or "").text or None,
        }
        for citation in result.citations
    ]
    if safe_citations:
        answer = "Relevant project documentation:\n" + "\n\n".join(
            f"{citation['snippet']}\n"
            f"[{citation['doc_title']}, section {citation['section'] or 'General'}, "
            f"chunk {citation['chunk_index']}]"
            for citation in safe_citations
        )
    else:
        answer = "No indexed documents were found for this project."
    egress = scan_egress(answer)
    return RAGQueryResponse(
        status="COMPLETED",
        answer=egress.text,
        citations=[CitationRead.model_validate(citation) for citation in safe_citations],
    )


@router.post("/projects/{order_id}/agent/run", response_model=AgentRunRead)
async def run_project_agent(
    order_id: UUID,
    payload: AgentRunRequest,
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> AgentRunRead:
    project = await _get_project(order_id, session, user)
    run = AgentRun(
        org_id=user.org_id,
        project_id=project.id,
        requested_by_id=user.id,
        mode=payload.mode,
        input_text=payload.input_text,
        status=AgentRunStatus.RUNNING,
    )
    session.add(run)
    await session.flush()
    started_at = perf_counter()
    state = await run_agent_workflow(
        session,
        run,
        org_id=user.org_id,
        project_id=project.id,
        mode=payload.mode,
        input_text=payload.input_text,
        action=payload.action,
    )
    run.latency_ms = round((perf_counter() - started_at) * 1000)
    run.input_tokens = max(1, len(payload.input_text) // 4)
    run.output_tokens = len(run.output_text or "") // 4
    task_type = {
        "srs": LLMTaskType.SRS_GENERATION,
        "scope": LLMTaskType.SCOPE_CHECK,
    }[payload.mode]
    if run.status != AgentRunStatus.BLOCKED:
        await record_llm_usage(
            session,
            org_id=user.org_id,
            project_id=project.id,
            agent_run_id=run.id,
            task_type=task_type,
            input_tokens=run.input_tokens,
            output_tokens=run.output_tokens,
            latency_ms=run.latency_ms,
        )
    approval_id = UUID(state["approval_id"]) if state.get("approval_id") else None
    await session.commit()
    await session.refresh(run)
    return _run_response(run, approval_id)


@router.get(
    "/approvals",
    response_model=list[ApprovalRead],
    dependencies=[Depends(require_roles(*staff_roles))],
)
async def list_approvals(
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
    pending_only: bool = True,
) -> list[ApprovalRead]:
    statement = select(ApprovalRequest).where(ApprovalRequest.org_id == user.org_id)
    if pending_only:
        statement = statement.where(ApprovalRequest.status == ApprovalStatus.PENDING)
    approvals = await session.scalars(statement.order_by(ApprovalRequest.created_at.desc()))
    return [_approval_response(approval) for approval in approvals]


@router.post(
    "/approvals/{approval_id}/resolve",
    response_model=ApprovalRead,
    dependencies=[Depends(require_roles(*staff_roles))],
)
async def resolve_approval(
    approval_id: UUID,
    payload: ApprovalResolveRequest,
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=80)],
) -> ApprovalRead:
    approval = await session.scalar(
        select(ApprovalRequest)
        .where(
            ApprovalRequest.id == approval_id,
            ApprovalRequest.org_id == user.org_id,
        )
        .with_for_update()
    )
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if idempotency_key != approval.idempotency_key:
        raise HTTPException(status_code=409, detail="Idempotency key does not match this approval")
    desired = ApprovalStatus(payload.decision.lower())
    if approval.status != ApprovalStatus.PENDING:
        if approval.status == desired:
            return _approval_response(approval)
        raise HTTPException(status_code=409, detail="Approval request was already resolved differently")

    approval.status = desired
    approval.reviewer_id = user.id
    approval.reviewer_notes = payload.reviewer_notes
    from datetime import datetime, timezone

    approval.resolved_at = datetime.now(timezone.utc)
    run = await session.scalar(
        select(AgentRun).where(
            AgentRun.id == approval.agent_run_id,
            AgentRun.org_id == user.org_id,
            AgentRun.project_id == approval.project_id,
        )
    )
    if run is not None:
        run.status = (
            AgentRunStatus.COMPLETED
            if desired == ApprovalStatus.APPROVED
            else AgentRunStatus.BLOCKED
        )
    if approval.action == ApprovalAction.INVOICE_DISPATCH:
        invoice_id_raw = approval.action_payload.get("invoice_id")
        if isinstance(invoice_id_raw, str):
            invoice = await session.scalar(
                select(Invoice).where(
                    Invoice.id == UUID(invoice_id_raw),
                    Invoice.org_id == user.org_id,
                    Invoice.project_id == approval.project_id,
                    Invoice.approval_request_id == approval.id,
                )
            )
            if invoice is not None:
                invoice.status = (
                    InvoiceStatus.ISSUED
                    if desired == ApprovalStatus.APPROVED
                    else InvoiceStatus.VOID
                )
    await session.commit()
    await session.refresh(approval)
    return _approval_response(approval)


async def _get_project(order_id: UUID, session: AsyncSession, user: User) -> ProjectOrder:
    statement = select(ProjectOrder).where(
        ProjectOrder.id == order_id,
        ProjectOrder.org_id == user.org_id,
    )
    if user.role == UserRole.CLIENT:
        if user.client_id is None:
            raise HTTPException(status_code=404, detail="Project order not found")
        statement = statement.join(Client).where(ProjectOrder.client_id == user.client_id)
    project = await session.scalar(statement)
    if project is None:
        raise HTTPException(status_code=404, detail="Project order not found")
    return project


def _run_response(run: AgentRun, approval_id: UUID | None) -> AgentRunRead:
    return AgentRunRead(
        id=run.id,
        org_id=run.org_id,
        project_id=run.project_id,
        status=run.status.value.upper(),
        mode=run.mode,
        scope_decision=run.scope_decision,
        risk_score=run.risk_score,
        generated_srs=run.generated_srs,
        milestones=run.milestones,
        output_text=run.output_text,
        citations=run.citations,
        input_tokens=run.input_tokens,
        output_tokens=run.output_tokens,
        latency_ms=run.latency_ms,
        approval_id=approval_id,
        created_at=run.created_at,
    )


def _approval_response(approval: ApprovalRequest) -> ApprovalRead:
    return ApprovalRead(
        id=approval.id,
        org_id=approval.org_id,
        project_id=approval.project_id,
        agent_run_id=approval.agent_run_id,
        action=approval.action.value.upper(),
        status=approval.status.value.upper(),
        idempotency_key=approval.idempotency_key,
        reviewer_notes=approval.reviewer_notes,
        resolved_at=approval.resolved_at,
        action_payload=approval.action_payload,
        created_at=approval.created_at,
    )

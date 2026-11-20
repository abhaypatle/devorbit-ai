import re
import secrets
from dataclasses import replace
from typing import Literal
from uuid import UUID

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.guardrails import GuardrailDecision, scan_egress, scan_ingress
from app.db.models import (
    ApprovalAction,
    ApprovalRequest,
    AgentRun,
    AgentRunStatus,
)
from app.rag.retriever import Citation, retrieve
from app.agent.state import AgentState

_WORD = re.compile(r"[a-z0-9]+", re.I)
_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "into", "is", "it", "of", "on", "or", "our", "the", "to", "we", "with",
}


async def guardrail_ingress(state: AgentState) -> dict[str, object]:
    result = scan_ingress(state["input_text"])
    if result.decision == GuardrailDecision.BLOCK:
        message = "Request blocked by the input safety guardrail."
        state["run"].status = AgentRunStatus.BLOCKED
        state["run"].output_text = message
        return {"status": "blocked", "sanitized_input": "", "output_text": message}
    return {"sanitized_input": result.text, "status": "running"}


async def rag_retrieve(state: AgentState) -> dict[str, object]:
    result = await retrieve(
        state["session"],
        org_id=state["org_id"],
        project_id=state["project_id"],
        query=state["sanitized_input"],
        approved_only=state["mode"] == "scope",
    )
    return {"context": result.context, "citations": list(result.citations)}


async def architect_or_scope_agent(state: AgentState) -> dict[str, object]:
    if state["mode"] == "srs":
        source_text = state["context"] or state["sanitized_input"]
        srs = (
            f"# Software Requirements Specification\n\n"
            f"## Project brief\n{source_text[:8000]}\n\n"
            "## Scope\nRequirements are derived from the supplied brief and cited project documents.\n\n"
            "## Assumptions and constraints\nValidate integrations, security, and acceptance criteria with the project owner.\n"
        )
        milestones = [
            {"name": "Discovery and acceptance criteria", "sequence": "1"},
            {"name": "Architecture and implementation", "sequence": "2"},
            {"name": "Verification and release", "sequence": "3"},
        ]
        return {
            "generated_srs": srs,
            "milestones": milestones,
            "scope_decision": "NEW_BRIEF",
            "risk_score": 25,
            "output_text": srs,
        }

    input_terms = _terms(state["sanitized_input"])
    evidence_terms = _terms(" ".join(citation.snippet for citation in state["citations"]))
    overlap = len(input_terms & evidence_terms) / max(1, len(input_terms))
    in_scope = bool(state["citations"]) and overlap >= 0.3
    decision = "IN_SCOPE" if in_scope else "CHANGE_REQUEST"
    risk_score = max(10, int(100 * (1.0 - overlap))) if in_scope else min(100, 60 + int(40 * (1.0 - overlap)))
    output = (
        f"Request classified as {decision} (risk score {risk_score}/100)."
        if in_scope
        else f"Request classified as {decision} (risk score {risk_score}/100); administrator approval is required."
    )
    return {
        "scope_decision": decision,
        "risk_score": risk_score,
        "output_text": output,
    }


async def risk_gate(state: AgentState) -> dict[str, object]:
    scope_change = state.get("scope_decision") == "CHANGE_REQUEST"
    action = state.get("action")
    if not scope_change and action is None:
        state["run"].status = AgentRunStatus.COMPLETED
        return {"status": "completed"}

    approval_action = action or ApprovalAction.CHANGE_REQUEST_QUOTE
    approval = ApprovalRequest(
        org_id=state["org_id"],
        project_id=state["project_id"],
        agent_run_id=state["run"].id,
        action=approval_action,
        idempotency_key=secrets.token_urlsafe(32),
        action_payload={
            "scope_decision": state.get("scope_decision", ""),
            "risk_score": state.get("risk_score", 0),
        },
    )
    state["session"].add(approval)
    await state["session"].flush()
    state["run"].status = AgentRunStatus.AWAITING_APPROVAL
    return {"status": "awaiting_approval", "approval_id": str(approval.id)}


async def finalize_response(state: AgentState) -> dict[str, object]:
    output = state.get("output_text", "")
    citations: list[Citation] = state["citations"]
    if citations:
        references = "\n\nSources:\n" + "\n".join(
            f"- [{citation.doc_title}, section {citation.section or 'General'}, "
            f"chunk {citation.chunk_index}]"
            for citation in citations
        )
        output += references
    state["run"].status = AgentRunStatus.COMPLETED
    state["run"].output_text = output
    return {"output_text": output, "status": "completed"}


async def guardrail_egress(state: AgentState) -> dict[str, object]:
    result = scan_egress(state.get("output_text", ""))
    citations = [
        replace(
            citation,
            doc_title=scan_egress(citation.doc_title).text,
            snippet=scan_egress(citation.snippet).text,
            section=scan_egress(citation.section or "").text or None,
        )
        for citation in state.get("citations", [])
    ]
    state["citations"] = citations
    state["run"].output_text = result.text
    state["run"].citations = [citation.as_dict() for citation in citations]
    generated_srs = state.get("generated_srs")
    state["run"].generated_srs = scan_egress(generated_srs).text if generated_srs else None
    state["run"].milestones = state.get("milestones")
    state["run"].scope_decision = state.get("scope_decision")
    state["run"].risk_score = state.get("risk_score")
    if state["run"].status == AgentRunStatus.RUNNING:
        state["run"].status = (
            AgentRunStatus.AWAITING_APPROVAL
            if state["status"] == "awaiting_approval"
            else AgentRunStatus.COMPLETED
        )
    return {
        "output_text": result.text,
        "citations": citations,
        "generated_srs": state["run"].generated_srs,
        "status": state["run"].status.value,
    }


def _terms(text: str) -> set[str]:
    return {term.casefold() for term in _WORD.findall(text) if term.casefold() not in _STOP_WORDS}


def _route_after_ingress(state: AgentState) -> Literal["rag_retrieve", "guardrail_egress"]:
    return "guardrail_egress" if state["status"] == "blocked" else "rag_retrieve"


def _route_after_risk(state: AgentState) -> Literal["finalize_response", "guardrail_egress"]:
    return "guardrail_egress" if state["status"] == "awaiting_approval" else "finalize_response"


def create_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("guardrail_ingress", guardrail_ingress)
    graph.add_node("rag_retrieve", rag_retrieve)
    graph.add_node("architect_or_scope_agent", architect_or_scope_agent)
    graph.add_node("risk_gate", risk_gate)
    graph.add_node("finalize_response", finalize_response)
    graph.add_node("guardrail_egress", guardrail_egress)
    graph.set_entry_point("guardrail_ingress")
    graph.add_conditional_edges(
        "guardrail_ingress",
        _route_after_ingress,
        {"rag_retrieve": "rag_retrieve", "guardrail_egress": "guardrail_egress"},
    )
    graph.add_edge("rag_retrieve", "architect_or_scope_agent")
    graph.add_edge("architect_or_scope_agent", "risk_gate")
    graph.add_conditional_edges(
        "risk_gate",
        _route_after_risk,
        {"finalize_response": "finalize_response", "guardrail_egress": "guardrail_egress"},
    )
    graph.add_edge("finalize_response", "guardrail_egress")
    graph.add_edge("guardrail_egress", END)
    return graph.compile()


async def run_agent_workflow(
    session: AsyncSession,
    run: AgentRun,
    *,
    org_id: UUID,
    project_id: UUID,
    mode: str,
    input_text: str,
    action: ApprovalAction | None = None,
) -> AgentState:
    state: AgentState = {
        "session": session,
        "run": run,
        "org_id": org_id,
        "project_id": project_id,
        "mode": mode,
        "input_text": input_text,
        "action": action,
        "status": "running",
        "sanitized_input": "",
        "context": "",
        "citations": [],
    }
    return await create_agent_graph().ainvoke(state)

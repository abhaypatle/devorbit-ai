import json

from fastapi import APIRouter, HTTPException, Request

from app.core.auth import get_current_user
from app.services.bedrock import analyze_with_bedrock
from app.services.github import normalize_workflow_event, verify_github_signature
from app.services.aws_security import inspect_aws_security
from fastapi import Depends
from app.models import User

router = APIRouter(prefix="/api", tags=["integrations"])


@router.post("/aws/security-audit")
def aws_security_audit(max_buckets: int = 50, user: User = Depends(get_current_user)) -> dict:
    if max_buckets < 1 or max_buckets > 100:
        raise HTTPException(status_code=422, detail="max_buckets must be between 1 and 100")
    try:
        return inspect_aws_security(max_buckets=max_buckets)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/architecture/ai-review")
async def architecture_ai_review(request: Request, user: User = Depends(get_current_user)) -> dict[str, str]:
    body = await request.json()
    try:
        return {"analysis": analyze_with_bedrock(body.get("nodes", []), body.get("edges", []))}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/webhooks/github")
async def github_webhook(request: Request) -> dict:
    payload = await request.body()
    if not verify_github_signature(payload, request.headers.get("x-hub-signature-256")):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    event = request.headers.get("x-github-event")
    if event != "workflow_run":
        return {"accepted": True, "ignored_event": event}
    return {"accepted": True, "event": normalize_workflow_event(json.loads(payload))}
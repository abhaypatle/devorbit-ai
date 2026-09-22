import hashlib
import hmac
import json

from app.core.config import get_settings


def verify_github_signature(payload: bytes, signature: str | None) -> bool:
    secret = get_settings().github_webhook_secret
    if not secret or not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def normalize_workflow_event(payload: dict) -> dict:
    workflow = payload.get("workflow_run", {})
    repository = payload.get("repository", {})
    return {"provider": "github", "event": "workflow_run", "action": payload.get("action"), "repository": repository.get("full_name"), "workflow": workflow.get("name"), "status": workflow.get("status"), "conclusion": workflow.get("conclusion"), "run_id": workflow.get("id")}
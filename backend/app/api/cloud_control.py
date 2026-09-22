from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.cloud_control import audit_security_config, generate_terraform, simulate_deploy

router = APIRouter(prefix="/api", tags=["cloud-control"])


class TerraformRequest(BaseModel):
    project_name: str = Field(default="devorbit", min_length=1, max_length=40)
    region: str = Field(default="us-east-1", pattern=r"^[a-z]{2}-[a-z]+-\d$")
    ec2_instances: int = Field(default=2, ge=1, le=20)
    vpc_cidr: str = Field(default="10.0.0.0/16", pattern=r"^\d{1,3}(?:\.\d{1,3}){3}/\d{1,2}$")
    s3_buckets: list[str] = Field(default_factory=lambda: ["artifacts"], max_length=10)
    enable_nat_gateway: bool = False


class AuditRequest(BaseModel):
    configuration: dict[str, Any] = Field(default_factory=dict)


class DeployRequest(BaseModel):
    target: str = Field(default="github-actions", pattern=r"^(github-actions|docker)$")
    branch: str = Field(default="main", min_length=1, max_length=100)


@router.post("/generate-terraform")
def generate_terraform_endpoint(request: TerraformRequest) -> dict[str, Any]:
    return {"status": "success", "filename": "main.tf", "terraform": generate_terraform(request.model_dump())}


@router.post("/ai-audit")
def ai_audit(request: AuditRequest) -> dict[str, Any]:
    findings = audit_security_config(request.configuration)
    return {"status": "success", "risk_level": "critical" if any(f["severity"] == "critical" for f in findings) else "high" if findings else "low", "findings": findings, "summary": f"{len(findings)} simulated finding(s) identified."}


@router.post("/deploy-trigger")
def deploy_trigger(request: DeployRequest) -> dict[str, Any]:
    return simulate_deploy(request.target, request.branch)
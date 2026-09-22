from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.academic import generate_capstone_documents

router = APIRouter(prefix="/api/modules", tags=["academic-modules"])


class CapstoneRequest(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    problem_statement: str = Field(min_length=20, max_length=3000)
    objectives: list[str] = Field(min_length=1, max_length=10)
    technologies: list[str] = Field(min_length=1, max_length=15)
    methodology: str = Field(default="Agile iterative development", min_length=3, max_length=160)
    authors: str = Field(default="DevOrbit AI Research Team", max_length=200)
    generation_mode: Literal["auto", "user_based"] = "auto"
    custom_outline: str = Field(default="", max_length=5000)


class StartupTask(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=3, max_length=240)
    description: str = Field(default="", max_length=2000)
    labels: list[str] = Field(default_factory=list, max_length=12)


class StartupSyncRequest(BaseModel):
    repository: str = Field(default="devorbit-ai/platform", min_length=3, max_length=200)
    tasks: list[StartupTask] = Field(default_factory=list, max_length=100)


class EnterpriseResource(BaseModel):
    resource_type: Literal["ec2", "rds", "s3", "alb", "nat_gateway", "lambda"]
    count: int = Field(default=1, ge=0, le=100)
    idle: bool = False


class EnterpriseAuditRequest(BaseModel):
    resources: list[EnterpriseResource] = Field(default_factory=list, max_length=100)
    controls: dict[str, bool] = Field(default_factory=dict)


@router.post("/capstone/generate")
def generate_capstone(request: CapstoneRequest) -> dict[str, Any]:
    if request.generation_mode == "user_based" and not request.custom_outline.strip():
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="custom_outline is required for user_based generation")
    return {"status": "success", "module": "capstone", "documents": generate_capstone_documents(request.model_dump())}


@router.post("/startup/sync-backlog")
def sync_startup_backlog(request: StartupSyncRequest) -> dict[str, Any]:
    """Simulate GitHub issues when no task payload is supplied, then allocate by skills."""
    source = "provided_tasks" if request.tasks else "simulated_github"
    tasks = request.tasks or [
        StartupTask(id="ISSUE-101", title="Build FastAPI authentication middleware", description="Add JWT validation, route protection, and security tests.", labels=["backend", "security"]),
        StartupTask(id="ISSUE-102", title="Create React cloud architecture canvas", description="Implement drag-and-drop AWS nodes and a responsive dashboard view.", labels=["frontend", "react"]),
        StartupTask(id="ISSUE-103", title="Configure GitHub Actions deployment workflow", description="Add Docker build, Terraform validation, and release notifications.", labels=["devops", "ci-cd"]),
        StartupTask(id="ISSUE-104", title="Add PostgreSQL persistence migrations", description="Create SQLAlchemy models and Alembic migrations for project data.", labels=["backend", "database"]),
        StartupTask(id="ISSUE-105", title="Write project security and API documentation", description="Document threat model, endpoints, and developer onboarding.", labels=["documentation"]),
    ]
    member_skills = {
        "Abhay": {"backend", "python", "fastapi", "security", "database", "postgresql", "architecture"},
        "Amit": {"frontend", "react", "typescript", "ui", "documentation", "testing"},
        "Rahul": {"devops", "ci-cd", "docker", "terraform", "aws", "infrastructure", "cloud"},
    }
    workloads = {member: 0 for member in member_skills}
    allocated: list[dict[str, Any]] = []
    for task in tasks:
        searchable = f"{task.title} {task.description} {' '.join(task.labels)}".lower()
        scores = {member: sum(1 for skill in skills if skill in searchable) for member, skills in member_skills.items()}
        assignee = max(member_skills, key=lambda member: (scores[member], -workloads[member]))
        workloads[assignee] += 1
        allocated.append({"task_id": task.id, "description": task.title, "details": task.description, "assignee": assignee, "status": "Allocated", "skill_score": scores[assignee], "labels": task.labels})
    return {"status": "success", "repository": request.repository, "source": source, "team": list(member_skills), "tasks": allocated, "summary": {"total": len(allocated), "by_assignee": workloads}}


@router.post("/enterprise/audit")
def enterprise_audit(request: EnterpriseAuditRequest) -> dict[str, Any]:
    resources = request.resources or [
        EnterpriseResource(resource_type="ec2", count=2),
        EnterpriseResource(resource_type="rds", count=1),
        EnterpriseResource(resource_type="s3", count=1),
        EnterpriseResource(resource_type="alb", count=1),
        EnterpriseResource(resource_type="nat_gateway", count=1),
    ]
    monthly_rates = {"ec2": 30.0, "rds": 65.0, "s3": 8.0, "alb": 30.0, "nat_gateway": 32.0, "lambda": 12.0}
    breakdown = [{"resource_type": resource.resource_type, "count": resource.count, "monthly_cost": round(monthly_rates[resource.resource_type] * resource.count, 2)} for resource in resources]
    monthly_cost = round(sum(item["monthly_cost"] for item in breakdown), 2)

    control_values = {"mfa_enabled": True, "cloudtrail_enabled": True, "s3_public_access_block": True, "security_groups_restricted": True}
    control_values.update(request.controls)
    checks = [
        {"control": "MFA enabled", "passed": control_values["mfa_enabled"], "recommendation": "Require MFA for human identities."},
        {"control": "CloudTrail enabled", "passed": control_values["cloudtrail_enabled"], "recommendation": "Enable organization-wide CloudTrail logging."},
        {"control": "S3 public access blocked", "passed": control_values["s3_public_access_block"], "recommendation": "Enable all S3 Block Public Access settings."},
        {"control": "Security groups restricted", "passed": control_values["security_groups_restricted"], "recommendation": "Restrict ingress and egress to required ports and CIDRs."},
    ]
    security_errors = sum(1 for check in checks if not check["passed"])
    return {
        "status": "success",
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "monthly_cost": monthly_cost,
        "currency": "USD",
        "cost_breakdown": breakdown,
        "security_errors": security_errors,
        "cis_status": "Compliant" if security_errors == 0 else "Action Required",
        "cis_checks": checks,
    }
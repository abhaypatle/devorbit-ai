from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.cloud_control import generate_terraform
from app.services.platform import analyze_architecture, forecast_cost, generate_iac, score_security, simulate_pipeline
from app.services.enterprise_features import analyze_finops, generate_multicloud_terraform, self_heal_iac

router = APIRouter(prefix="/api", tags=["enterprise-platform"])


class ArchitectureRequest(BaseModel):
    nodes: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    edges: list[dict[str, Any]] = Field(default_factory=list, max_length=200)


class IacRequest(BaseModel):
    project_name: str = Field(default="devorbit", min_length=1, max_length=40)
    region: str = "us-east-1"
    ec2_instances: int = Field(default=1, ge=1, le=20)
    vpc_cidr: str = "10.0.0.0/16"
    s3_buckets: list[str] = Field(default_factory=lambda: ["artifacts"])
    enable_nat_gateway: bool = False
    output_format: Literal["terraform", "cloudformation"] = "terraform"
    cloud_provider: Literal["aws", "azure", "gcp"] = "aws"


class PipelineRequest(BaseModel):
    action: Literal["connect", "scan", "deploy"]
    provider: Literal["github", "gitlab"] = "github"
    repository: str = Field(min_length=3, max_length=200)
    branch: str = Field(default="main", min_length=1, max_length=100)


class SecurityRequest(BaseModel):
    configuration: dict[str, Any] = Field(default_factory=dict)


class CostRequest(BaseModel):
    resources: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    months: int = Field(default=6, ge=1, le=24)


class FinOpsRequest(BaseModel):
    request: str = Field(default="Find idle resources and right-size compute", max_length=1000)
    resources: list[dict[str, Any]] = Field(default_factory=list, max_length=100)


class IaCValidationRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1_000_000)
    output_format: Literal["terraform", "cloudformation"] = "terraform"


@router.post("/architecture/analyze")
def architecture_analyze(request: ArchitectureRequest) -> dict[str, Any]:
    return analyze_architecture(request.nodes, request.edges)


@router.post("/generate-iac")
def generate_iac_endpoint(request: IacRequest) -> dict[str, Any]:
    requirements = request.model_dump(exclude={"output_format"})
    result = generate_iac(requirements, request.output_format, generate_multicloud_terraform if request.output_format == "terraform" else generate_terraform)
    if request.output_format == "terraform":
        healed = self_heal_iac(result["content"], request.output_format)
        result["content"] = healed["content"]
        result["validation"] = healed
    return result


@router.post("/pipeline/action")
def pipeline_action(request: PipelineRequest) -> dict[str, Any]:
    return simulate_pipeline(request.action, request.provider, request.repository, request.branch)


@router.post("/security/score")
def security_score(request: SecurityRequest) -> dict[str, Any]:
    return score_security(request.configuration)


@router.post("/cost/forecast")
def cost_forecast(request: CostRequest) -> dict[str, Any]:
    return forecast_cost(request.resources, request.months)


@router.post("/finops/optimize")
def finops_optimize(request: FinOpsRequest) -> dict[str, Any]:
    resources = request.resources or [{"name": "web-fleet", "type": "ec2", "instance_type": "t3.medium", "count": 2}, {"name": "idle-worker", "type": "ec2", "instance_type": "m5.large", "count": 1, "idle": True}]
    return analyze_finops(resources, request.request)


@router.post("/iac/self-heal")
def iac_self_heal(request: IaCValidationRequest) -> dict[str, Any]:
    return self_heal_iac(request.content, request.output_format)
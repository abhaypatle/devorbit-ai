"""Pure, provider-neutral platform logic for DevOrbit's enterprise demo APIs."""

from datetime import datetime, timezone
import json
import re
from typing import Any


def _name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower() or "resource"


def analyze_architecture(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    types = {str(node.get("type", "")).lower() for node in nodes}
    suggestions: list[dict[str, str]] = []
    if "ec2" in types and "vpc" not in types:
        suggestions.append({"severity": "high", "title": "EC2 is outside an explicit VPC boundary", "recommendation": "Add a VPC, private subnets, route tables, and security groups."})
    if "rds" in types and "ec2" in types and len(edges) < 2:
        suggestions.append({"severity": "medium", "title": "Database connectivity is underspecified", "recommendation": "Connect RDS through private subnets and a least-privilege database security group."})
    if "s3" in types and "cloudfront" not in types:
        suggestions.append({"severity": "low", "title": "Object delivery can be optimized", "recommendation": "Consider CloudFront for cacheable public assets and origin access control."})
    if len([node for node in nodes if str(node.get("type", "")).lower() == "ec2"]) > 1 and "elb" not in types:
        suggestions.append({"severity": "medium", "title": "Multiple compute nodes lack a load balancer", "recommendation": "Add an Application Load Balancer and health checks."})
    if not suggestions:
        suggestions.append({"severity": "info", "title": "Architecture baseline looks coherent", "recommendation": "Run the security audit and validate the generated plan before deployment."})
    return {"node_count": len(nodes), "edge_count": len(edges), "services": sorted(types), "suggestions": suggestions}


def generate_cloudformation(requirements: dict[str, Any]) -> dict[str, Any]:
    project = _name(requirements.get("project_name", "devorbit"))
    region = requirements.get("region", "us-east-1")
    instances = int(requirements.get("ec2_instances", 1))
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": f"DevOrbit generated infrastructure for {project}",
        "Parameters": {"Environment": {"Type": "String", "Default": "production"}},
        "Resources": {
            "Vpc": {"Type": "AWS::EC2::VPC", "Properties": {"CidrBlock": requirements.get("vpc_cidr", "10.0.0.0/16"), "Tags": [{"Key": "Name", "Value": f"{project}-vpc"}]}},
            "WebSecurityGroup": {"Type": "AWS::EC2::SecurityGroup", "Properties": {"GroupDescription": "DevOrbit web ingress", "VpcId": {"Ref": "Vpc"}, "SecurityGroupIngress": [{"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80, "CidrIp": "0.0.0.0/0"}]}},
        },
        "Metadata": {"DevOrbit": {"region": region, "requested_instance_count": instances, "review_required": True}},
    }


def generate_iac(requirements: dict[str, Any], output_format: str, terraform_generator: Any) -> dict[str, Any]:
    if output_format == "cloudformation":
        template = generate_cloudformation(requirements)
        return {"filename": "template.json", "content": json.dumps(template, indent=2), "content_type": "application/json"}
    return {"filename": "main.tf", "content": terraform_generator(requirements), "content_type": "text/plain"}


def simulate_pipeline(action: str, provider: str, repository: str, branch: str = "main") -> dict[str, Any]:
    run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    steps = {"connect": ["repository validated", "webhook registration simulated"], "scan": ["Dockerfile parsed", "simulated Trivy scan completed", "no image pushed"], "deploy": ["approval gate checked", "deployment queued", "no cloud mutation performed"]}
    return {"status": "simulated", "action": action, "provider": provider, "repository": repository, "branch": branch, "run_id": run_id, "steps": steps.get(action, [])}


def score_security(configuration: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    def check(key: str, bad: bool, title: str, severity: str, remediation: str) -> None:
        checks.append({"control": key, "status": "fail" if bad else "pass", "title": title, "severity": severity if bad else "none", "remediation": remediation})
    check("iam_mfa", configuration.get("mfa_enabled") is False, "MFA is not enforced", "critical", "Require MFA through an IAM policy and identity center.")
    check("iam_wildcard", bool(configuration.get("iam_wildcard_actions")), "IAM policy grants wildcard actions", "critical", "Replace wildcard actions and resources with task-specific permissions.")
    check("sg_ingress", bool(configuration.get("open_ingress")), "Security group allows broad ingress", "high", "Restrict source CIDRs and expose only required ports.")
    check("s3_public", bool(configuration.get("public_buckets")), "S3 public access is enabled", "critical", "Enable Block Public Access and review bucket policies.")
    check("cloudtrail", configuration.get("cloudtrail_enabled") is False, "CloudTrail is disabled", "medium", "Enable organization-wide CloudTrail with protected log storage.")
    failed = [item for item in checks if item["status"] == "fail"]
    score = max(0, 100 - sum({"critical": 30, "high": 20, "medium": 10}[item["severity"]] for item in failed))
    return {"score": score, "risk": "critical" if score < 50 else "high" if score < 75 else "moderate" if score < 90 else "low", "checks": checks, "failed_controls": len(failed)}


def forecast_cost(resources: list[dict[str, Any]], months: int) -> dict[str, Any]:
    rates = {"ec2": 30.0, "rds": 65.0, "s3": 8.0, "lambda": 12.0, "nat": 32.0}
    current = round(sum(rates.get(str(item.get("type", "")).lower(), 10.0) * max(1, int(item.get("count", 1))) for item in resources), 2)
    idle_savings = round(sum(rates.get(str(item.get("type", "")).lower(), 0.0) for item in resources if item.get("idle")), 2)
    projection = [{"month": index + 1, "estimate": round(current * ((1.0 + 0.025) ** index), 2)} for index in range(months)]
    return {"current_monthly_estimate": current, "forecast": projection, "recommendations": [{"title": "Review idle resources", "monthly_savings": idle_savings, "action": "Stop or right-size resources marked idle."}] if idle_savings else [{"title": "Add utilization telemetry", "monthly_savings": 0, "action": "Connect CloudWatch metrics before rightsizing."}]}
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings


def _finding(service: str, severity: str, title: str, remediation: str, evidence: Any = None) -> dict[str, Any]:
    return {"service": service, "severity": severity, "title": title, "remediation": remediation, "evidence": evidence}


def inspect_aws_security(max_buckets: int = 50) -> dict[str, Any]:
    """Inspect AWS through the default boto3 credential chain; never accepts keys from a request."""
    settings = get_settings()
    session = boto3.Session(region_name=settings.aws_region)
    findings: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    try:
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        checks.append({"control": "aws_identity", "status": "pass", "account": identity.get("Account"), "arn": identity.get("Arn")})
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError("AWS credentials are unavailable or invalid") from exc

    iam = session.client("iam")
    try:
        password_policy = iam.get_account_password_policy().get("PasswordPolicy", {})
        if not password_policy.get("RequireUppercaseCharacters") or not password_policy.get("RequireNumbers"):
            findings.append(_finding("iam", "medium", "Weak account password policy", "Require upper/lowercase characters, numbers, symbols, and rotation."))
    except iam.exceptions.NoSuchEntityException:
        findings.append(_finding("iam", "high", "Account password policy is not configured", "Configure an IAM account password policy for human identities."))
    try:
        users = iam.list_users(MaxItems=100).get("Users", [])
        for user in users:
            keys = iam.list_access_keys(UserName=user["UserName"]).get("AccessKeyMetadata", [])
            for key in keys:
                if key.get("Status") == "Active":
                    findings.append(_finding("iam", "high", f"Active long-lived access key for {user['UserName']}", "Replace user keys with short-lived IAM role credentials.", {"created": str(key.get("CreateDate"))}))
    except (BotoCoreError, ClientError) as exc:
        findings.append(_finding("iam", "medium", "IAM user inspection incomplete", "Grant the execution role least-privilege read-only audit permissions.", str(exc)))

    s3 = session.client("s3")
    try:
        buckets = s3.list_buckets().get("Buckets", [])[:max_buckets]
        for bucket in buckets:
            name = bucket["Name"]
            try:
                block = s3.get_public_access_block(Bucket=name).get("PublicAccessBlockConfiguration", {})
                if not all(block.get(key, False) for key in ("BlockPublicAcls", "BlockPublicPolicy", "IgnorePublicAcls", "RestrictPublicBuckets")):
                    findings.append(_finding("s3", "critical", f"S3 Block Public Access is incomplete for {name}", "Enable all four S3 Block Public Access controls.", block))
            except ClientError as exc:
                if exc.response.get("Error", {}).get("Code") == "NoSuchPublicAccessBlockConfiguration":
                    findings.append(_finding("s3", "critical", f"S3 public access block is missing for {name}", "Enable account and bucket-level S3 Block Public Access."))
    except (BotoCoreError, ClientError) as exc:
        findings.append(_finding("s3", "medium", "S3 inspection incomplete", "Grant s3:ListAllMyBuckets and read-only bucket policy permissions.", str(exc)))

    ec2 = session.client("ec2")
    try:
        groups = ec2.describe_security_groups().get("SecurityGroups", [])
        for group in groups:
            for permission in group.get("IpPermissions", []):
                if any(ip.get("CidrIp") == "0.0.0.0/0" for ip in permission.get("IpRanges", [])):
                    findings.append(_finding("ec2", "high", f"Security group {group.get('GroupId')} allows global ingress", "Restrict ingress to known CIDRs and required ports.", {"from": permission.get("FromPort"), "to": permission.get("ToPort")}))
    except (BotoCoreError, ClientError) as exc:
        findings.append(_finding("ec2", "medium", "Security group inspection incomplete", "Grant ec2:DescribeSecurityGroups to the audit role.", str(exc)))
    return {"provider": "aws", "region": settings.aws_region, "checks": checks, "findings": findings, "finding_count": len(findings)}
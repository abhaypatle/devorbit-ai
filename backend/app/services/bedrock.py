import json
from typing import Any

import boto3

from app.core.config import get_settings


def analyze_with_bedrock(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
    settings = get_settings()
    if not settings.bedrock_enabled:
        raise RuntimeError("Bedrock integration is disabled; set BEDROCK_ENABLED=true after granting the execution role access")
    client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    prompt = "Analyze this cloud architecture JSON. Return concise prioritized reliability, security, and cost recommendations. Do not invent deployed resources.\n" + json.dumps({"nodes": nodes, "edges": edges}, separators=(",", ":"))
    response = client.converse(modelId=settings.bedrock_model_id, messages=[{"role": "user", "content": [{"text": prompt}]}], inferenceConfig={"maxTokens": 1200, "temperature": 0.2})
    return response["output"]["message"]["content"][0]["text"]
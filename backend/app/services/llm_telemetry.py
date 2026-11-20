from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import LLMTaskType, LLMUsageLog


def estimate_llm_cost(
    *,
    provider: str,
    model_name: str,
    input_tokens: int,
    output_tokens: int,
) -> Decimal:
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("Token counts cannot be negative")
    settings = get_settings()
    rates = settings.llm_provider_pricing.get(
        f"{provider}:{model_name}",
        settings.llm_provider_pricing.get(
            provider,
            {
                "input_per_million_usd": settings.llm_input_price_per_million_usd,
                "output_per_million_usd": settings.llm_output_price_per_million_usd,
            },
        ),
    )
    input_rate = Decimal(str(rates.get("input_per_million_usd", 0)))
    output_rate = Decimal(str(rates.get("output_per_million_usd", 0)))
    if input_rate < 0 or output_rate < 0:
        raise ValueError("LLM pricing rates cannot be negative")
    cost = (
        Decimal(input_tokens) * input_rate + Decimal(output_tokens) * output_rate
    ) / Decimal(1_000_000)
    return cost.quantize(Decimal("0.00000001"))


async def record_llm_usage(
    session: AsyncSession,
    *,
    org_id: UUID,
    project_id: UUID,
    agent_run_id: UUID,
    task_type: LLMTaskType,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    provider: str | None = None,
    model_name: str | None = None,
) -> LLMUsageLog:
    if latency_ms < 0:
        raise ValueError("Latency cannot be negative")
    settings = get_settings()
    selected_provider = provider or settings.llm_default_provider
    selected_model = model_name or settings.llm_default_model
    usage = LLMUsageLog(
        org_id=org_id,
        project_id=project_id,
        agent_run_id=agent_run_id,
        provider=selected_provider,
        model_name=selected_model,
        task_type=task_type,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        estimated_cost_usd=estimate_llm_cost(
            provider=selected_provider,
            model_name=selected_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        ),
    )
    session.add(usage)
    return usage

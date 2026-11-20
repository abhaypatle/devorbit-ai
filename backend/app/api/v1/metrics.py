from decimal import Decimal
from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.dependencies import DbSession, require_roles
from app.db.models import (
    Invoice,
    InvoiceStatus,
    LLMUsageLog,
    ProjectOrder,
    Subscription,
    SubscriptionStatus,
    User,
    UserRole,
)
from app.finops_schemas import ProjectMetricsResponse

router = APIRouter(tags=["metrics"])
staff_access = Depends(require_roles(UserRole.ADMIN, UserRole.ENGINEER))


@router.get(
    "/projects/{order_id}/metrics",
    response_model=ProjectMetricsResponse,
    dependencies=[staff_access],
)
async def project_metrics(
    order_id: UUID,
    session: DbSession,
    user: Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.ENGINEER))],
) -> ProjectMetricsResponse:
    project = await session.scalar(
        select(ProjectOrder).where(
            ProjectOrder.id == order_id,
            ProjectOrder.org_id == user.org_id,
        )
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project order not found")

    usage_rows = list(
        (
            await session.scalars(
                select(LLMUsageLog).where(
                    LLMUsageLog.org_id == user.org_id,
                    LLMUsageLog.project_id == project.id,
                )
            )
        ).all()
    )
    invoices = list(
        (
            await session.scalars(
                select(Invoice).where(
                    Invoice.org_id == user.org_id,
                    Invoice.project_id == project.id,
                )
            )
        ).all()
    )
    subscriptions = list(
        (
            await session.scalars(
                select(Subscription).where(
                    Subscription.org_id == user.org_id,
                    Subscription.project_id == project.id,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                )
            )
        ).all()
    )

    input_tokens = sum(row.input_tokens for row in usage_rows)
    output_tokens = sum(row.output_tokens for row in usage_rows)
    total_cost = sum((Decimal(row.estimated_cost_usd) for row in usage_rows), Decimal("0"))
    latencies = sorted(row.latency_ms for row in usage_rows)
    average_latency = sum(latencies) / len(latencies) if latencies else 0.0
    p95_latency = latencies[max(0, ceil(len(latencies) * 0.95) - 1)] if latencies else 0
    issued_revenue = sum(
        invoice.amount_cents
        for invoice in invoices
        if invoice.status in {InvoiceStatus.ISSUED, InvoiceStatus.PAID}
    )
    paid_revenue = sum(
        invoice.amount_cents for invoice in invoices if invoice.status == InvoiceStatus.PAID
    )
    mrr = sum(_monthly_cents(item.amount, item.interval.value) for item in subscriptions)
    contract_budget = int((Decimal(project.budget) * 100).quantize(Decimal("1")))
    margin_cents = contract_budget - int((total_cost * 100).quantize(Decimal("1")))
    margin_percent = (
        float(Decimal(margin_cents) / Decimal(contract_budget) * 100)
        if contract_budget
        else None
    )

    return ProjectMetricsResponse(
        org_id=user.org_id,
        project_id=project.id,
        currency=project.currency,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        estimated_llm_cost_usd=float(total_cost),
        average_latency_ms=round(average_latency, 2),
        p95_latency_ms=p95_latency,
        contract_budget_cents=contract_budget,
        issued_revenue_cents=issued_revenue,
        paid_revenue_cents=paid_revenue,
        active_subscription_mrr_cents=mrr,
        estimated_margin_cents=margin_cents,
        estimated_margin_percent=margin_percent,
    )


def _monthly_cents(amount: Decimal, interval: str) -> int:
    monthly_amount = Decimal(amount)
    if interval == "quarterly":
        monthly_amount /= Decimal(3)
    elif interval == "yearly":
        monthly_amount /= Decimal(12)
    return int((monthly_amount * 100).quantize(Decimal("1")))

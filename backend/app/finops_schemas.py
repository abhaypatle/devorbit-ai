from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    client_id: UUID
    project_id: UUID
    subscription_id: UUID | None
    invoice_number: str
    status: str
    amount_cents: int
    subtotal_cents: int
    tax_cents: int
    currency: str
    due_date: date
    billing_period_start: date | None
    billing_period_end: date | None
    line_items: list[dict[str, object]]
    pdf_storage_key: str | None
    approval_request_id: UUID | None
    paid_at: datetime | None
    payment_reference: str | None
    created_at: datetime


class BillingRunResponse(BaseModel):
    created: int
    invoices: list[InvoiceRead]


class PaymentWebhookResponse(BaseModel):
    event_id: str
    invoice_id: UUID
    status: str


class ProjectMetricsResponse(BaseModel):
    org_id: UUID
    project_id: UUID
    currency: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_llm_cost_usd: float
    average_latency_ms: float
    p95_latency_ms: int
    contract_budget_cents: int
    issued_revenue_cents: int
    paid_revenue_cents: int
    active_subscription_mrr_cents: int
    estimated_margin_cents: int
    estimated_margin_percent: float | None

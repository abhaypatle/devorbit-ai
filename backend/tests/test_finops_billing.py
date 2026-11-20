import hashlib
import hmac
import json
from datetime import date
from decimal import Decimal
from httpx import AsyncClient

from app.core.config import get_settings
from app.db.models import BillingInterval
from app.services.billing_engine import advance_billing_date
from app.services.llm_telemetry import estimate_llm_cost


async def setup_workspace(client: AsyncClient, slug: str) -> tuple[str, str, str]:
    registered = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": f"FinOps {slug}",
            "organization_slug": slug,
            "full_name": "Billing Admin",
            "email": f"admin@{slug}.example.com",
            "password": "secure-test-password-123",
        },
    )
    assert registered.status_code == 201, registered.text
    token = registered.json()["access_token"]
    org_id = registered.json()["user"]["org_id"]
    headers = {"Authorization": f"Bearer {token}"}
    client_record = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"name": "FinOps Customer", "email": f"client@{slug}.example.com"},
    )
    assert client_record.status_code == 201, client_record.text
    order = await client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "client_id": client_record.json()["id"],
            "project_key": f"{slug.upper()}-PROJECT",
            "name": "Billing project",
            "budget": "1000.00",
        },
    )
    assert order.status_code == 201, order.text
    return token, org_id, order.json()["id"]


async def test_subscription_billing_pdf_approval_and_cycle_idempotency(
    client: AsyncClient,
) -> None:
    token, _, project_id = await setup_workspace(client, "billing-cycle")
    headers = {"Authorization": f"Bearer {token}"}
    period_start = date(2026, 1, 31)
    subscription = await client.post(
        "/api/v1/subscriptions",
        headers=headers,
        json={
            "project_id": project_id,
            "name": "Quarterly platform support",
            "amount": "250.00",
            "currency": "USD",
            "interval": "quarterly",
            "next_billing_date": period_start.isoformat(),
        },
    )
    assert subscription.status_code == 201, subscription.text
    run = await client.post(
        "/api/v1/billing/run-due?as_of_date=2026-01-31",
        headers=headers,
    )
    assert run.status_code == 200, run.text
    assert run.json()["created"] == 1
    invoice = run.json()["invoices"][0]
    assert invoice["status"] == "pending_approval"
    assert invoice["amount_cents"] == 25_000
    assert invoice["billing_period_start"] == "2026-01-31"
    assert invoice["billing_period_end"] == "2026-04-29"
    assert advance_billing_date(period_start, BillingInterval.QUARTERLY) == date(2026, 4, 30)

    repeated = await client.post(
        "/api/v1/billing/run-due?as_of_date=2026-01-31",
        headers=headers,
    )
    assert repeated.status_code == 200
    assert repeated.json()["created"] == 0
    assert repeated.json()["invoices"] == []

    download = await client.get(
        f"/api/v1/invoices/{invoice['id']}/download",
        headers=headers,
    )
    assert download.status_code == 200
    assert download.content.startswith(b"%PDF-")

    approvals = await client.get("/api/v1/approvals", headers=headers)
    approval = next(
        item for item in approvals.json() if item["id"] == invoice["approval_request_id"]
    )
    assert approval["action"] == "INVOICE_DISPATCH"
    resolved = await client.post(
        f"/api/v1/approvals/{approval['id']}/resolve",
        headers={
            **headers,
            "Idempotency-Key": approval["idempotency_key"],
        },
        json={"decision": "APPROVED", "reviewer_notes": "Invoice validated"},
    )
    assert resolved.status_code == 200, resolved.text
    invoice_after = await client.get(f"/api/v1/invoices/{invoice['id']}", headers=headers)
    assert invoice_after.json()["status"] == "issued"

    advanced = await client.post(
        "/api/v1/billing/run-due?as_of_date=2026-04-30",
        headers=headers,
    )
    assert advanced.status_code == 200
    assert advanced.json()["created"] == 1
    assert advanced.json()["invoices"][0]["billing_period_start"] == "2026-04-30"


async def test_payment_webhook_hmac_and_idempotent_paid_state(
    client: AsyncClient,
    monkeypatch,
) -> None:
    token, _, project_id = await setup_workspace(client, "payment-webhook")
    headers = {"Authorization": f"Bearer {token}"}
    settings = get_settings()
    monkeypatch.setattr(settings, "require_approval_for_invoices", False)
    monkeypatch.setattr(settings, "invoice_approval_threshold_cents", 999_999_999)
    monkeypatch.setattr(settings, "payment_webhook_secret", "webhook-secret-for-tests")

    subscription = await client.post(
        "/api/v1/subscriptions",
        headers=headers,
        json={
            "project_id": project_id,
            "name": "Monthly hosting",
            "amount": "75.00",
            "interval": "monthly",
            "next_billing_date": "2026-06-01",
        },
    )
    assert subscription.status_code == 201
    run = await client.post(
        "/api/v1/billing/run-due?as_of_date=2026-06-01",
        headers=headers,
    )
    assert run.status_code == 200
    invoice = run.json()["invoices"][0]
    assert invoice["status"] == "issued"
    body = json.dumps(
        {
            "event_id": "evt-payment-one",
            "invoice_id": invoice["id"],
            "payment_reference": "pay-ref-001",
        },
        separators=(",", ":"),
    ).encode()
    invalid = await client.post(
        "/api/v1/webhooks/payments",
        content=body,
        headers={"X-Signature": "sha256=invalid"},
    )
    assert invalid.status_code == 401

    signature = hmac.new(
        b"webhook-secret-for-tests", body, hashlib.sha256
    ).hexdigest()
    valid_headers = {"X-Signature": f"sha256={signature}"}
    paid = await client.post(
        "/api/v1/webhooks/payments",
        content=body,
        headers=valid_headers,
    )
    assert paid.status_code == 200, paid.text
    assert paid.json()["status"] == "PAID"
    replay = await client.post(
        "/api/v1/webhooks/payments",
        content=body,
        headers=valid_headers,
    )
    assert replay.status_code == 200
    assert replay.json()["status"] == "PAID"
    invoice_after = await client.get(f"/api/v1/invoices/{invoice['id']}", headers=headers)
    assert invoice_after.json()["status"] == "paid"
    assert invoice_after.json()["payment_reference"] == "pay-ref-001"


async def test_usage_cost_estimation_and_project_metrics_isolation(
    client: AsyncClient,
    monkeypatch,
) -> None:
    token_a, _, project_a = await setup_workspace(client, "metrics-tenant-a")
    token_b, _, _ = await setup_workspace(client, "metrics-tenant-b")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_provider_pricing", {})
    monkeypatch.setattr(settings, "llm_input_price_per_million_usd", 2.0)
    monkeypatch.setattr(settings, "llm_output_price_per_million_usd", 10.0)
    monkeypatch.setattr(settings, "require_approval_for_invoices", False)
    monkeypatch.setattr(settings, "invoice_approval_threshold_cents", 999_999_999)
    assert estimate_llm_cost(
        provider="local",
        model_name="test-model",
        input_tokens=1_000_000,
        output_tokens=500_000,
    ) == Decimal("7.00000000")

    agent = await client.post(
        f"/api/v1/projects/{project_a}/agent/run",
        headers=headers_a,
        json={"mode": "srs", "input_text": "Build a subscription billing dashboard."},
    )
    assert agent.status_code == 200
    subscription = await client.post(
        "/api/v1/subscriptions",
        headers=headers_a,
        json={
            "project_id": project_a,
            "name": "Monthly operations",
            "amount": "50.00",
            "interval": "monthly",
            "next_billing_date": "2026-01-01",
        },
    )
    assert subscription.status_code == 201
    billing = await client.post(
        "/api/v1/billing/run-due?as_of_date=2026-01-01",
        headers=headers_a,
    )
    assert billing.status_code == 200
    assert billing.json()["invoices"][0]["status"] == "issued"
    metrics = await client.get(f"/api/v1/projects/{project_a}/metrics", headers=headers_a)
    assert metrics.status_code == 200, metrics.text
    result = metrics.json()
    assert result["total_tokens"] == result["input_tokens"] + result["output_tokens"]
    assert result["input_tokens"] > 0
    assert result["estimated_llm_cost_usd"] > 0
    assert result["contract_budget_cents"] == 100_000
    assert result["issued_revenue_cents"] == 5_000
    assert result["active_subscription_mrr_cents"] == 5_000
    assert result["estimated_margin_cents"] <= result["contract_budget_cents"]
    assert result["average_latency_ms"] >= 0
    assert result["p95_latency_ms"] >= 0

    denied = await client.get(
        f"/api/v1/projects/{project_a}/metrics",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert denied.status_code == 404

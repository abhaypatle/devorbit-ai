import calendar
import hashlib
import hmac
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import (
    ApprovalAction,
    ApprovalRequest,
    ApprovalStatus,
    BillingInterval,
    Client,
    Invoice,
    InvoiceStatus,
    Organization,
    PaymentWebhookEvent,
    ProjectOrder,
    Subscription,
    SubscriptionStatus,
)
from app.services.pdf_invoice import (
    InvoiceLineItem,
    calculate_tax_cents,
    generate_invoice_pdf,
)
from app.services.s3_storage import storage


def advance_billing_date(current: date, interval: BillingInterval) -> date:
    months = {
        BillingInterval.MONTHLY: 1,
        BillingInterval.QUARTERLY: 3,
        BillingInterval.YEARLY: 12,
    }[interval]
    month_index = current.month - 1 + months
    year = current.year + month_index // 12
    month = month_index % 12 + 1
    day = min(current.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


async def run_due_subscriptions(
    session: AsyncSession,
    as_of_date: date,
    *,
    org_id: UUID | None = None,
) -> list[Invoice]:
    statement = (
        select(Subscription, ProjectOrder, Client, Organization)
        .join(
            ProjectOrder,
            (ProjectOrder.id == Subscription.project_id)
            & (ProjectOrder.org_id == Subscription.org_id),
        )
        .join(
            Client,
            (Client.id == ProjectOrder.client_id)
            & (Client.org_id == ProjectOrder.org_id),
        )
        .join(Organization, Organization.id == Subscription.org_id)
        .where(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.next_billing_date.is_not(None),
            Subscription.next_billing_date <= as_of_date,
        )
        .order_by(Subscription.next_billing_date, Subscription.id)
        .with_for_update(of=Subscription)
    )
    if org_id is not None:
        statement = statement.where(Subscription.org_id == org_id)
    rows = (await session.execute(statement)).all()
    created: list[Invoice] = []
    for subscription, project, client, organization in rows:
        billing_date = subscription.next_billing_date
        if billing_date is None:
            continue
        idempotency_key = f"subscription:{subscription.id}:{billing_date.isoformat()}"
        existing = await session.scalar(
            select(Invoice).where(Invoice.idempotency_key == idempotency_key)
        )
        next_date = advance_billing_date(billing_date, subscription.interval)
        if existing is not None:
            subscription.next_billing_date = next_date
            await session.commit()
            continue

        subtotal = int((Decimal(subscription.amount) * 100).quantize(Decimal("1")))
        tax = calculate_tax_cents(subtotal)
        invoice_id = uuid4()
        line_items: list[dict[str, object]] = [
            {
                "description": subscription.name,
                "quantity": "1",
                "unit_amount_cents": subtotal,
            }
        ]
        amount = subtotal + tax
        settings = get_settings()
        requires_approval = (
            settings.require_approval_for_invoices
            or amount >= settings.invoice_approval_threshold_cents
        )
        invoice = Invoice(
            id=invoice_id,
            org_id=subscription.org_id,
            client_id=project.client_id,
            project_id=project.id,
            subscription_id=subscription.id,
            invoice_number=f"DO-{billing_date:%Y%m%d}-{invoice_id.hex[:10].upper()}",
            status=InvoiceStatus.PENDING_APPROVAL if requires_approval else InvoiceStatus.ISSUED,
            idempotency_key=idempotency_key,
            amount_cents=amount,
            subtotal_cents=subtotal,
            tax_cents=tax,
            currency=subscription.currency,
            due_date=as_of_date + timedelta(days=settings.invoice_due_days),
            billing_period_start=billing_date,
            billing_period_end=next_date - timedelta(days=1),
            line_items=line_items,
        )
        session.add(invoice)
        subscription.next_billing_date = next_date
        await session.flush()

        if requires_approval:
            approval = ApprovalRequest(
                org_id=invoice.org_id,
                project_id=invoice.project_id,
                agent_run_id=None,
                action=ApprovalAction.INVOICE_DISPATCH,
                status=ApprovalStatus.PENDING,
                idempotency_key=f"invoice:{invoice.idempotency_key}"[:80],
                action_payload={
                    "invoice_id": str(invoice.id),
                    "amount_cents": amount,
                    "currency": invoice.currency,
                },
            )
            session.add(approval)
            await session.flush()
            invoice.approval_request_id = approval.id

        pdf = generate_invoice_pdf(
            invoice=invoice,
            organization=organization,
            client=client,
            project=project,
            line_items=[
                InvoiceLineItem(
                    description=subscription.name,
                    quantity=Decimal("1"),
                    unit_amount_cents=subtotal,
                )
            ],
        )
        key = (
            f"{invoice.org_id}/{invoice.project_id}/invoices/"
            f"{invoice.id}.pdf"
        )
        uploaded_key = await storage.upload(key, pdf, content_type="application/pdf")
        invoice.pdf_storage_key = uploaded_key
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            await storage.delete(uploaded_key)
            duplicate = await session.scalar(
                select(Invoice).where(Invoice.idempotency_key == idempotency_key)
            )
            if duplicate is None:
                raise
            created.append(duplicate)
            continue
        await session.refresh(invoice)
        created.append(invoice)
    return created


def verify_payment_signature(payload: bytes, signature: str, secret: str) -> bool:
    supplied = signature.removeprefix("sha256=").strip()
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(supplied, expected)


async def confirm_payment(
    session: AsyncSession,
    *,
    event_id: str,
    invoice_id: UUID,
    payment_reference: str,
) -> Invoice:
    previous_event = await session.get(PaymentWebhookEvent, event_id)
    if previous_event is not None:
        if previous_event.invoice_id != invoice_id:
            raise ValueError("Payment event id was already used for a different invoice")
        invoice = await session.get(Invoice, invoice_id)
        if invoice is None:
            raise LookupError("Invoice not found")
        return invoice

    invoice = await session.scalar(
        select(Invoice).where(Invoice.id == invoice_id).with_for_update()
    )
    if invoice is None:
        raise LookupError("Invoice not found")
    if invoice.status == InvoiceStatus.PENDING_APPROVAL:
        raise ValueError("Invoice cannot be paid before it is issued")
    if invoice.status == InvoiceStatus.VOID:
        raise ValueError("Void invoices cannot be paid")

    session.add(PaymentWebhookEvent(event_id=event_id, invoice_id=invoice.id))
    if invoice.status != InvoiceStatus.PAID:
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = datetime.now(timezone.utc)
        invoice.payment_reference = payment_reference
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        previous_event = await session.get(PaymentWebhookEvent, event_id)
        if previous_event is None or previous_event.invoice_id != invoice_id:
            raise
        invoice = await session.get(Invoice, invoice_id)
        if invoice is None:
            raise LookupError("Invoice not found")
        return invoice
    await session.refresh(invoice)
    return invoice


def payment_event_payload(
    raw: bytes,
) -> dict[str, Any]:
    try:
        result = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Webhook body must be valid JSON") from exc
    if not isinstance(result, dict):
        raise ValueError("Webhook body must be a JSON object")
    event_id = result.get("event_id")
    payment_reference = result.get("payment_reference")
    if not isinstance(event_id, str) or not event_id or len(event_id) > 160:
        raise ValueError("event_id is required and must be at most 160 characters")
    if not isinstance(payment_reference, str) or not payment_reference or len(payment_reference) > 160:
        raise ValueError("payment_reference is required and must be at most 160 characters")
    try:
        invoice_id = UUID(str(result["invoice_id"]))
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError("invoice_id must be a valid UUID") from exc
    return {
        "event_id": event_id,
        "invoice_id": invoice_id,
        "payment_reference": payment_reference,
    }

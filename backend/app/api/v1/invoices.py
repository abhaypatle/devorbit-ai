import json
from datetime import date
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import select

from app.core.config import get_settings
from app.core.dependencies import DbSession, get_current_user, require_roles
from app.db.models import Invoice, User, UserRole
from app.finops_schemas import BillingRunResponse, InvoiceRead, PaymentWebhookResponse
from app.services.billing_engine import (
    confirm_payment,
    payment_event_payload,
    run_due_subscriptions,
    verify_payment_signature,
)
from app.services.s3_storage import storage

router = APIRouter(tags=["billing", "invoices", "webhooks"])


@router.post(
    "/billing/run-due",
    response_model=BillingRunResponse,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def run_due_billing(
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
    as_of_date: date | None = None,
) -> BillingRunResponse:
    invoices = await run_due_subscriptions(
        session, as_of_date or date.today(), org_id=user.org_id
    )
    return BillingRunResponse(
        created=len(invoices),
        invoices=[InvoiceRead.model_validate(invoice) for invoice in invoices],
    )


@router.get("/invoices", response_model=list[InvoiceRead])
async def list_invoices(
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> list[InvoiceRead]:
    statement = select(Invoice).where(Invoice.org_id == user.org_id)
    if user.role == UserRole.CLIENT:
        if user.client_id is None:
            return []
        statement = statement.where(Invoice.client_id == user.client_id)
    invoices = await session.scalars(statement.order_by(Invoice.created_at.desc()))
    return [InvoiceRead.model_validate(invoice) for invoice in invoices]


@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: UUID,
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> InvoiceRead:
    return InvoiceRead.model_validate(await _get_invoice(invoice_id, session, user))


@router.get("/invoices/{invoice_id}/download")
async def download_invoice(
    invoice_id: UUID,
    session: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> Response:
    invoice = await _get_invoice(invoice_id, session, user)
    if invoice.pdf_storage_key is None:
        raise HTTPException(status_code=404, detail="Invoice PDF is not available")
    if get_settings().storage_mode == "s3":
        return RedirectResponse(
            await storage.download_reference(invoice.pdf_storage_key),
            status_code=307,
        )
    try:
        content = await storage.read(invoice.pdf_storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Invoice PDF is not available") from exc
    return StreamingResponse(
        iter([content]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(invoice.invoice_number)}.pdf"
        },
    )


@router.post("/webhooks/payments", response_model=PaymentWebhookResponse)
async def payment_webhook(
    request: Request,
    session: DbSession,
    signature: Annotated[str, Header(alias="X-Signature")],
) -> PaymentWebhookResponse:
    secret = get_settings().payment_webhook_secret
    if not secret:
        raise HTTPException(status_code=503, detail="Payment webhook secret is not configured")
    raw_body = await request.body()
    if not verify_payment_signature(raw_body, signature, secret):
        raise HTTPException(status_code=401, detail="Invalid payment webhook signature")
    try:
        event = payment_event_payload(raw_body)
        invoice = await confirm_payment(session, **event)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PaymentWebhookResponse(
        event_id=event["event_id"],
        invoice_id=invoice.id,
        status=invoice.status.value.upper(),
    )


async def _get_invoice(invoice_id: UUID, session: DbSession, user: User) -> Invoice:
    statement = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.org_id == user.org_id,
    )
    if user.role == UserRole.CLIENT:
        if user.client_id is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        statement = statement.where(Invoice.client_id == user.client_id)
    invoice = await session.scalar(statement)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

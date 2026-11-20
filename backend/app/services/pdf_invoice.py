from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import get_settings
from app.db.models import Invoice, Organization, Client, ProjectOrder


@dataclass(frozen=True)
class InvoiceLineItem:
    description: str
    quantity: Decimal
    unit_amount_cents: int

    @property
    def total_cents(self) -> int:
        return int(self.quantity * self.unit_amount_cents)


def generate_invoice_pdf(
    *,
    invoice: Invoice,
    organization: Organization,
    client: Client,
    project: ProjectOrder,
    line_items: list[InvoiceLineItem],
    payment_status: str | None = None,
) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title=f"Invoice {invoice.invoice_number}",
        author=organization.name,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="InvoiceRight", parent=styles["Normal"], alignment=TA_RIGHT))
    story = [
        Paragraph("INVOICE", styles["Title"]),
        Paragraph(f"<b>{escape(organization.name)}</b>", styles["Heading2"]),
        Paragraph(escape(invoice.invoice_number), styles["Normal"]),
        Spacer(1, 16),
        Paragraph("<b>Bill to</b>", styles["Heading3"]),
        Paragraph(escape(client.name), styles["Normal"]),
    ]
    if client.company:
        story.append(Paragraph(escape(client.company), styles["Normal"]))
    story.extend(
        [
            Paragraph(escape(client.email), styles["Normal"]),
            Spacer(1, 12),
            Paragraph(f"<b>Project</b>: {escape(project.project_key)} — {escape(project.name)}", styles["Normal"]),
            Paragraph(
                f"<b>Billing period</b>: {_format_date(invoice.billing_period_start)} – "
                f"{_format_date(invoice.billing_period_end)}",
                styles["Normal"],
            ),
            Paragraph(f"<b>Due date</b>: {invoice.due_date.isoformat()}", styles["Normal"]),
            Paragraph(
                f"<b>Payment status</b>: {escape(payment_status or invoice.status.value.upper())}",
                styles["Normal"],
            ),
            Spacer(1, 16),
        ]
    )

    rows = [["Description", "Qty", "Unit price", "Amount"]]
    for line in line_items:
        rows.append(
            [
                Paragraph(escape(line.description), styles["Normal"]),
                str(line.quantity.normalize()),
                _money(line.unit_amount_cents, invoice.currency),
                _money(line.total_cents, invoice.currency),
            ]
        )
    rows.extend(
        [
            ["", "", "Subtotal", _money(invoice.subtotal_cents, invoice.currency)],
            ["", "", "Tax", _money(invoice.tax_cents, invoice.currency)],
            ["", "", "Total", _money(invoice.amount_cents, invoice.currency)],
        ]
    )
    table = Table(rows, colWidths=[3.45 * inch, 0.6 * inch, 1.15 * inch, 1.15 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -4), 0.35, colors.HexColor("#CBD5E1")),
                ("LINEABOVE", (2, -3), (-1, -3), 0.7, colors.HexColor("#64748B")),
                ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (2, -1), (-1, -1), colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    document.build(story)
    return buffer.getvalue()


def lines_from_invoice(invoice: Invoice) -> list[InvoiceLineItem]:
    lines: list[InvoiceLineItem] = []
    for item in invoice.line_items:
        lines.append(
            InvoiceLineItem(
                description=str(item["description"]),
                quantity=Decimal(str(item.get("quantity", 1))),
                unit_amount_cents=int(item["unit_amount_cents"]),
            )
        )
    return lines


def calculate_tax_cents(subtotal_cents: int, tax_rate: float | None = None) -> int:
    rate = Decimal(str(get_settings().default_tax_rate if tax_rate is None else tax_rate))
    if subtotal_cents < 0 or rate < 0:
        raise ValueError("Subtotal and tax rate cannot be negative")
    return int((Decimal(subtotal_cents) * rate).quantize(Decimal("1")))


def _format_date(value: date | None) -> str:
    return value.isoformat() if value else "—"


def _money(amount_cents: int, currency: str) -> str:
    amount = Decimal(amount_cents) / 100
    return f"{currency.upper()} {amount:,.2f}"

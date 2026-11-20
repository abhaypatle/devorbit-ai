"""Add LLM telemetry and recurring subscription invoices.

Revision ID: 0003_checkpoint_three
Revises: 0002_checkpoint_two
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_checkpoint_three"
down_revision = "0002_checkpoint_two"
branch_labels = None
depends_on = None

invoice_status = postgresql.ENUM(
    "draft", "pending_approval", "issued", "paid", "void",
    name="invoice_status",
    create_type=False,
)
llm_task_type = postgresql.ENUM(
    "srs_generation", "rag_qa", "scope_check", name="llm_task_type", create_type=False
)


def upgrade() -> None:
    op.execute("ALTER TYPE billing_interval ADD VALUE IF NOT EXISTS 'quarterly'")
    op.execute(
        "CREATE TYPE invoice_status AS ENUM "
        "('draft', 'pending_approval', 'issued', 'paid', 'void')"
    )
    op.execute(
        "CREATE TYPE llm_task_type AS ENUM ('srs_generation', 'rag_qa', 'scope_check')"
    )

    op.add_column("subscriptions", sa.Column("next_billing_date", sa.Date(), nullable=True))
    op.execute(
        "UPDATE subscriptions SET next_billing_date = CURRENT_DATE "
        "WHERE status = 'active' AND next_billing_date IS NULL"
    )
    op.create_unique_constraint("uq_subscriptions_id_org", "subscriptions", ["id", "org_id"])
    op.create_unique_constraint(
        "uq_orders_id_tenant_client", "project_orders", ["id", "org_id", "client_id"]
    )
    op.create_unique_constraint(
        "uq_approvals_scope", "approval_requests", ["id", "org_id", "project_id"]
    )
    op.alter_column("approval_requests", "agent_run_id", nullable=True)

    op.create_table(
        "invoices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("subscription_id", sa.Uuid(), nullable=True),
        sa.Column("invoice_number", sa.String(length=48), nullable=False),
        sa.Column("status", invoice_status, nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("subtotal_cents", sa.Integer(), nullable=False),
        sa.Column("tax_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("billing_period_start", sa.Date(), nullable=True),
        sa.Column("billing_period_end", sa.Date(), nullable=True),
        sa.Column("line_items", sa.JSON(), nullable=False),
        sa.Column("pdf_storage_key", sa.String(length=700), nullable=True),
        sa.Column("approval_request_id", sa.Uuid(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_reference", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["client_id", "org_id"], ["clients.id", "clients.org_id"], name="fk_invoices_client_same_org", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id", "org_id", "client_id"], ["project_orders.id", "project_orders.org_id", "project_orders.client_id"], name="fk_invoices_project_same_org", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subscription_id", "org_id"], ["subscriptions.id", "subscriptions.org_id"], name="fk_invoices_subscription_same_scope", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approval_request_id", "org_id", "project_id"], ["approval_requests.id", "approval_requests.org_id", "approval_requests.project_id"], name="fk_invoices_approval_same_scope", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "org_id", "client_id", "project_id", name="uq_invoices_scope"),
        sa.UniqueConstraint("idempotency_key", name="uq_invoices_idempotency"),
        sa.UniqueConstraint("invoice_number"),
    )
    op.create_index("ix_invoices_client_id", "invoices", ["client_id"], unique=False)
    op.create_index("ix_invoices_org_id", "invoices", ["org_id"], unique=False)
    op.create_index("ix_invoices_project_id", "invoices", ["project_id"], unique=False)
    op.create_index("ix_invoices_subscription_id", "invoices", ["subscription_id"], unique=False)

    op.create_table(
        "llm_usage_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("agent_run_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model_name", sa.String(length=160), nullable=False),
        sa.Column("task_type", llm_task_type, nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Numeric(precision=14, scale=8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["agent_run_id", "org_id", "project_id"], ["agent_runs.id", "agent_runs.org_id", "agent_runs.project_id"], name="fk_llm_usage_run_same_scope", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id", "org_id"], ["project_orders.id", "project_orders.org_id"], name="fk_llm_usage_project_same_org", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_llm_usage_logs_agent_run_id", "llm_usage_logs", ["agent_run_id"], unique=False)
    op.create_index("ix_llm_usage_logs_org_id", "llm_usage_logs", ["org_id"], unique=False)
    op.create_index("ix_llm_usage_logs_project_id", "llm_usage_logs", ["project_id"], unique=False)

    op.create_table(
        "payment_webhook_events",
        sa.Column("event_id", sa.String(length=160), nullable=False),
        sa.Column("invoice_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_payment_webhook_events_invoice_id", "payment_webhook_events", ["invoice_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_payment_webhook_events_invoice_id", table_name="payment_webhook_events")
    op.drop_table("payment_webhook_events")
    op.drop_index("ix_llm_usage_logs_project_id", table_name="llm_usage_logs")
    op.drop_index("ix_llm_usage_logs_org_id", table_name="llm_usage_logs")
    op.drop_index("ix_llm_usage_logs_agent_run_id", table_name="llm_usage_logs")
    op.drop_table("llm_usage_logs")
    op.drop_index("ix_invoices_subscription_id", table_name="invoices")
    op.drop_index("ix_invoices_project_id", table_name="invoices")
    op.drop_index("ix_invoices_org_id", table_name="invoices")
    op.drop_index("ix_invoices_client_id", table_name="invoices")
    op.drop_table("invoices")
    op.execute("DELETE FROM approval_requests WHERE agent_run_id IS NULL")
    op.alter_column("approval_requests", "agent_run_id", nullable=False)
    op.drop_constraint("uq_approvals_scope", "approval_requests", type_="unique")
    op.drop_constraint("uq_orders_id_tenant_client", "project_orders", type_="unique")
    op.drop_constraint("uq_subscriptions_id_org", "subscriptions", type_="unique")
    op.drop_column("subscriptions", "next_billing_date")
    op.execute("DROP TYPE llm_task_type")
    op.execute("DROP TYPE invoice_status")

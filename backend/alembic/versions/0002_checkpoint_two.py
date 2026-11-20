"""Add project documents, RAG chunks, agent runs, and approvals.

Revision ID: 0002_checkpoint_two
Revises: 0001_checkpoint_one
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision = "0002_checkpoint_two"
down_revision = "0001_checkpoint_one"
branch_labels = None
depends_on = None

document_status = postgresql.ENUM(
    "indexed", "failed", name="document_status", create_type=False
)
agent_run_status = postgresql.ENUM(
    "running", "completed", "awaiting_approval", "blocked", "failed",
    name="agent_run_status",
    create_type=False,
)
approval_action = postgresql.ENUM(
    "change_request_quote", "invoice_dispatch",
    name="approval_action",
    create_type=False,
)
approval_status = postgresql.ENUM(
    "pending", "approved", "rejected", name="approval_status", create_type=False
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_unique_constraint("uq_users_id_org", "users", ["id", "org_id"])
    op.execute("CREATE TYPE document_status AS ENUM ('indexed', 'failed')")
    op.execute(
        "CREATE TYPE agent_run_status AS ENUM "
        "('running', 'completed', 'awaiting_approval', 'blocked', 'failed')"
    )
    op.execute(
        "CREATE TYPE approval_action AS ENUM ('change_request_quote', 'invoice_dispatch')"
    )
    op.execute("CREATE TYPE approval_status AS ENUM ('pending', 'approved', 'rejected')")

    op.create_table(
        "project_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=160), nullable=False),
        sa.Column("storage_key", sa.String(length=700), nullable=False),
        sa.Column("is_approved", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("status", document_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id", "org_id"], ["project_orders.id", "project_orders.org_id"], name="fk_documents_project_same_org", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_id", "org_id"], ["users.id", "users.org_id"], name="fk_documents_uploader_same_org", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "org_id", "project_id", name="uq_documents_id_tenant_project"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_project_documents_org_id", "project_documents", ["org_id"], unique=False)
    op.create_index("ix_project_documents_project_id", "project_documents", ["project_id"], unique=False)

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_id", sa.Uuid(), nullable=False),
        sa.Column("status", agent_run_status, nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("generated_srs", sa.Text(), nullable=True),
        sa.Column("milestones", sa.JSON(), nullable=True),
        sa.Column("scope_decision", sa.String(length=32), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id", "org_id"], ["project_orders.id", "project_orders.org_id"], name="fk_agent_runs_project_same_org", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_id", "org_id"], ["users.id", "users.org_id"], name="fk_agent_runs_requester_same_org", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "org_id", "project_id", name="uq_agent_runs_id_tenant_project"),
    )
    op.create_index("ix_agent_runs_org_id", "agent_runs", ["org_id"], unique=False)
    op.create_index("ix_agent_runs_project_id", "agent_runs", ["project_id"], unique=False)

    op.create_table(
        "approval_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("agent_run_id", sa.Uuid(), nullable=False),
        sa.Column("action", approval_action, nullable=False),
        sa.Column("status", approval_status, nullable=False),
        sa.Column("idempotency_key", sa.String(length=80), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("action_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["agent_run_id", "org_id", "project_id"], ["agent_runs.id", "agent_runs.org_id", "agent_runs.project_id"], name="fk_approvals_agent_run_same_tenant_project", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id", "org_id"], ["project_orders.id", "project_orders.org_id"], name="fk_approvals_project_same_org", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id", "org_id"], ["users.id", "users.org_id"], name="fk_approvals_reviewer_same_org"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_approval_idempotency_key"),
    )
    op.create_index("ix_approval_requests_agent_run_id", "approval_requests", ["agent_run_id"], unique=False)
    op.create_index("ix_approval_requests_org_id", "approval_requests", ["org_id"], unique=False)
    op.create_index("ix_approval_requests_project_id", "approval_requests", ["project_id"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("doc_id", sa.Uuid(), nullable=False),
        sa.Column("doc_title", sa.String(length=240), nullable=False),
        sa.Column("section", sa.String(length=240), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["doc_id", "org_id", "project_id"], ["project_documents.id", "project_documents.org_id", "project_documents.project_id"], name="fk_chunks_document_same_tenant_project", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_chunks_doc_id", "document_chunks", ["doc_id"], unique=False)
    op.create_index("ix_document_chunks_org_id", "document_chunks", ["org_id"], unique=False)
    op.create_index("ix_document_chunks_project_id", "document_chunks", ["project_id"], unique=False)
    op.create_index(
        "ix_document_chunks_scope",
        "document_chunks",
        ["org_id", "project_id", "doc_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_document_chunks_scope", table_name="document_chunks")
    op.drop_index("ix_document_chunks_project_id", table_name="document_chunks")
    op.drop_index("ix_document_chunks_org_id", table_name="document_chunks")
    op.drop_index("ix_document_chunks_doc_id", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_index("ix_approval_requests_project_id", table_name="approval_requests")
    op.drop_index("ix_approval_requests_org_id", table_name="approval_requests")
    op.drop_index("ix_approval_requests_agent_run_id", table_name="approval_requests")
    op.drop_table("approval_requests")
    op.drop_index("ix_agent_runs_project_id", table_name="agent_runs")
    op.drop_index("ix_agent_runs_org_id", table_name="agent_runs")
    op.drop_table("agent_runs")
    op.drop_index("ix_project_documents_project_id", table_name="project_documents")
    op.drop_index("ix_project_documents_org_id", table_name="project_documents")
    op.drop_table("project_documents")
    op.drop_constraint("uq_users_id_org", "users", type_="unique")
    op.execute("DROP TYPE approval_status")
    op.execute("DROP TYPE approval_action")
    op.execute("DROP TYPE agent_run_status")
    op.execute("DROP TYPE document_status")

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    JSON,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class UserRole(StrEnum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    CLIENT = "client"


class OrderStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BillingInterval(StrEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class DocumentStatus(StrEnum):
    INDEXED = "indexed"
    FAILED = "failed"


class AgentRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    AWAITING_APPROVAL = "awaiting_approval"
    BLOCKED = "blocked"
    FAILED = "failed"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalAction(StrEnum):
    CHANGE_REQUEST_QUOTE = "change_request_quote"
    INVOICE_DISPATCH = "invoice_dispatch"


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ISSUED = "issued"
    PAID = "paid"
    VOID = "void"


class LLMTaskType(StrEnum):
    SRS_GENERATION = "srs_generation"
    RAG_QA = "rag_qa"
    SCOPE_CHECK = "scope_check"


VectorStorage = JSON().with_variant(Vector(), "postgresql")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PaymentWebhookEvent(Base):
    __tablename__ = "payment_webhook_events"

    event_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    invoice_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="organization", passive_deletes="all")
    clients: Mapped[list["Client"]] = relationship(back_populates="organization", passive_deletes="all")
    orders: Mapped[list["ProjectOrder"]] = relationship(back_populates="organization", passive_deletes="all")
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="organization", passive_deletes="all"
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("org_id", "email", name="uq_users_org_email"),
        UniqueConstraint("id", "org_id", name="uq_users_id_org"),
        ForeignKeyConstraint(
            ["client_id", "org_id"],
            ["clients.id", "clients.org_id"],
            name="fk_users_client_same_org",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    client_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped[Organization] = relationship(back_populates="users")
    client: Mapped["Client | None"] = relationship(
        back_populates="users", foreign_keys=[client_id]
    )


class Client(TimestampMixin, Base):
    __tablename__ = "clients"
    __table_args__ = (
        UniqueConstraint("org_id", "email", name="uq_clients_org_email"),
        UniqueConstraint("id", "org_id", name="uq_clients_id_org"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    company: Mapped[str | None] = mapped_column(String(160))
    notes: Mapped[str | None] = mapped_column(Text)

    organization: Mapped[Organization] = relationship(back_populates="clients")
    users: Mapped[list[User]] = relationship(
        back_populates="client", foreign_keys="User.client_id"
    )
    orders: Mapped[list["ProjectOrder"]] = relationship(
        back_populates="client", passive_deletes="all", overlaps="orders"
    )


class ProjectOrder(TimestampMixin, Base):
    __tablename__ = "project_orders"
    __table_args__ = (
        UniqueConstraint("org_id", "project_key", name="uq_orders_org_project_key"),
        UniqueConstraint("id", "org_id", name="uq_orders_id_org"),
        UniqueConstraint("id", "org_id", "client_id", name="uq_orders_id_tenant_client"),
        ForeignKeyConstraint(
            ["client_id", "org_id"],
            ["clients.id", "clients.org_id"],
            name="fk_project_orders_client_same_org",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    client_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    project_key: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status", values_callable=lambda enum: [item.value for item in enum]),
        default=OrderStatus.DRAFT,
        nullable=False,
    )
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    organization: Mapped[Organization] = relationship(
        back_populates="orders", overlaps="client,orders"
    )
    client: Mapped[Client] = relationship(
        back_populates="orders", overlaps="organization,orders"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="project", passive_deletes="all", overlaps="organization,subscriptions"
    )


class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("id", "org_id", "project_id", name="uq_subscriptions_id_scope"),
        UniqueConstraint("id", "org_id", name="uq_subscriptions_id_org"),
        ForeignKeyConstraint(
            ["project_id", "org_id"],
            ["project_orders.id", "project_orders.org_id"],
            name="fk_subscriptions_project_same_org",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    interval: Mapped[BillingInterval] = mapped_column(
        Enum(
            BillingInterval,
            name="billing_interval",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(
            SubscriptionStatus,
            name="subscription_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
    )
    next_billing_date: Mapped[date | None] = mapped_column(Date)

    organization: Mapped[Organization] = relationship(
        back_populates="subscriptions", overlaps="project"
    )
    project: Mapped[ProjectOrder] = relationship(
        back_populates="subscriptions", overlaps="organization,subscriptions"
    )


class ProjectDocument(TimestampMixin, Base):
    __tablename__ = "project_documents"
    __table_args__ = (
        UniqueConstraint("id", "org_id", "project_id", name="uq_documents_id_tenant_project"),
        ForeignKeyConstraint(
            ["project_id", "org_id"],
            ["project_orders.id", "project_orders.org_id"],
            name="fk_documents_project_same_org",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["uploaded_by_id", "org_id"],
            ["users.id", "users.org_id"],
            name="fk_documents_uploader_same_org",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    project_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    uploaded_by_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(160), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(700), unique=True, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(
            DocumentStatus,
            name="document_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=DocumentStatus.INDEXED,
        nullable=False,
    )

    project: Mapped[ProjectOrder] = relationship()
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )


class DocumentChunk(TimestampMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["doc_id", "org_id", "project_id"],
            ["project_documents.id", "project_documents.org_id", "project_documents.project_id"],
            name="fk_chunks_document_same_tenant_project",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    project_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    doc_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    doc_title: Mapped[str] = mapped_column(String(240), nullable=False)
    section: Mapped[str | None] = mapped_column(String(240))
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(VectorStorage, nullable=False)

    document: Mapped[ProjectDocument] = relationship(back_populates="chunks")


class AgentRun(TimestampMixin, Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        UniqueConstraint("id", "org_id", "project_id", name="uq_agent_runs_id_tenant_project"),
        ForeignKeyConstraint(
            ["project_id", "org_id"],
            ["project_orders.id", "project_orders.org_id"],
            name="fk_agent_runs_project_same_org",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["requested_by_id", "org_id"],
            ["users.id", "users.org_id"],
            name="fk_agent_runs_requester_same_org",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    project_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    requested_by_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[AgentRunStatus] = mapped_column(
        Enum(
            AgentRunStatus,
            name="agent_run_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=AgentRunStatus.RUNNING,
        nullable=False,
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    generated_srs: Mapped[str | None] = mapped_column(Text)
    milestones: Mapped[list[dict[str, str]] | None] = mapped_column(JSON)
    scope_decision: Mapped[str | None] = mapped_column(String(32))
    risk_score: Mapped[int | None] = mapped_column()
    citations: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    output_text: Mapped[str | None] = mapped_column(Text)
    input_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(default=0, nullable=False)

    project: Mapped[ProjectOrder] = relationship()


class ApprovalRequest(TimestampMixin, Base):
    __tablename__ = "approval_requests"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_approval_idempotency_key"),
        UniqueConstraint("id", "org_id", "project_id", name="uq_approvals_scope"),
        ForeignKeyConstraint(
            ["project_id", "org_id"],
            ["project_orders.id", "project_orders.org_id"],
            name="fk_approvals_project_same_org",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["agent_run_id", "org_id", "project_id"],
            ["agent_runs.id", "agent_runs.org_id", "agent_runs.project_id"],
            name="fk_approvals_agent_run_same_tenant_project",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["reviewer_id", "org_id"],
            ["users.id", "users.org_id"],
            name="fk_approvals_reviewer_same_org",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    project_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    agent_run_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    action: Mapped[ApprovalAction] = mapped_column(
        Enum(
            ApprovalAction,
            name="approval_action",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(
            ApprovalStatus,
            name="approval_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=ApprovalStatus.PENDING,
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(String(80), nullable=False)
    reviewer_id: Mapped[UUID | None] = mapped_column(Uuid)
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    action_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("id", "org_id", "client_id", "project_id", name="uq_invoices_scope"),
        UniqueConstraint("idempotency_key", name="uq_invoices_idempotency"),
        ForeignKeyConstraint(
            ["client_id", "org_id"],
            ["clients.id", "clients.org_id"],
            name="fk_invoices_client_same_org",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["project_id", "org_id", "client_id"],
            ["project_orders.id", "project_orders.org_id", "project_orders.client_id"],
            name="fk_invoices_project_same_org",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["subscription_id", "org_id"],
            ["subscriptions.id", "subscriptions.org_id"],
            name="fk_invoices_subscription_same_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["approval_request_id", "org_id", "project_id"],
            ["approval_requests.id", "approval_requests.org_id", "approval_requests.project_id"],
            name="fk_invoices_approval_same_scope",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    client_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    project_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    subscription_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    invoice_number: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(
            InvoiceStatus,
            name="invoice_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=InvoiceStatus.DRAFT,
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    amount_cents: Mapped[int] = mapped_column(nullable=False)
    subtotal_cents: Mapped[int] = mapped_column(nullable=False)
    tax_cents: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period_start: Mapped[date | None] = mapped_column(Date)
    billing_period_end: Mapped[date | None] = mapped_column(Date)
    line_items: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    pdf_storage_key: Mapped[str | None] = mapped_column(String(700))
    approval_request_id: Mapped[UUID | None] = mapped_column(Uuid, unique=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payment_reference: Mapped[str | None] = mapped_column(String(160))

    client: Mapped[Client] = relationship(viewonly=True)
    project: Mapped[ProjectOrder] = relationship(viewonly=True)
    subscription: Mapped[Subscription | None] = relationship(viewonly=True)


class LLMUsageLog(TimestampMixin, Base):
    __tablename__ = "llm_usage_logs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "org_id"],
            ["project_orders.id", "project_orders.org_id"],
            name="fk_llm_usage_project_same_org",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["agent_run_id", "org_id", "project_id"],
            ["agent_runs.id", "agent_runs.org_id", "agent_runs.project_id"],
            name="fk_llm_usage_run_same_scope",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    project_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    agent_run_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model_name: Mapped[str] = mapped_column(String(160), nullable=False)
    task_type: Mapped[LLMTaskType] = mapped_column(
        Enum(
            LLMTaskType,
            name="llm_task_type",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    input_tokens: Mapped[int] = mapped_column(nullable=False)
    output_tokens: Mapped[int] = mapped_column(nullable=False)
    latency_ms: Mapped[int] = mapped_column(nullable=False)
    estimated_cost_usd: Mapped[Decimal] = mapped_column(Numeric(14, 8), nullable=False)


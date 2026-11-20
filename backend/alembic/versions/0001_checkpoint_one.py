"""Create tenant, identity, client, order, and subscription tables.

Revision ID: 0001_checkpoint_one
Revises:
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_checkpoint_one"
down_revision = None
branch_labels = None
depends_on = None

user_role = postgresql.ENUM(
    "admin", "engineer", "client", name="user_role", create_type=False
)
order_status = postgresql.ENUM(
    "draft", "active", "on_hold", "completed", "cancelled",
    name="order_status",
    create_type=False,
)
billing_interval = postgresql.ENUM(
    "monthly", "yearly", name="billing_interval", create_type=False
)
subscription_status = postgresql.ENUM(
    "active", "paused", "cancelled", name="subscription_status", create_type=False
)


def upgrade() -> None:
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'engineer', 'client')")
    op.execute(
        "CREATE TYPE order_status AS ENUM ('draft', 'active', 'on_hold', 'completed', 'cancelled')"
    )
    op.execute("CREATE TYPE billing_interval AS ENUM ('monthly', 'yearly')")
    op.execute("CREATE TYPE subscription_status AS ENUM ('active', 'paused', 'cancelled')")

    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=False)

    op.create_table(
        "clients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("company", sa.String(length=160), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "org_id", name="uq_clients_id_org"),
        sa.UniqueConstraint("org_id", "email", name="uq_clients_org_email"),
    )
    op.create_index("ix_clients_org_id", "clients", ["org_id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["client_id", "org_id"], ["clients.id", "clients.org_id"], name="fk_users_client_same_org"),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_id", "email", name="uq_users_org_email"),
    )
    op.create_index("ix_users_client_id", "users", ["client_id"], unique=False)
    op.create_index("ix_users_org_id", "users", ["org_id"], unique=False)

    op.create_table(
        "project_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("project_key", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", order_status, nullable=False),
        sa.Column("budget", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["client_id", "org_id"], ["clients.id", "clients.org_id"], name="fk_project_orders_client_same_org", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "org_id", name="uq_orders_id_org"),
        sa.UniqueConstraint("org_id", "project_key", name="uq_orders_org_project_key"),
    )
    op.create_index("ix_project_orders_client_id", "project_orders", ["client_id"], unique=False)
    op.create_index("ix_project_orders_org_id", "project_orders", ["org_id"], unique=False)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("interval", billing_interval, nullable=False),
        sa.Column("status", subscription_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id", "org_id"], ["project_orders.id", "project_orders.org_id"], name="fk_subscriptions_project_same_org", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscriptions_org_id", "subscriptions", ["org_id"], unique=False)
    op.create_index("ix_subscriptions_project_id", "subscriptions", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_subscriptions_project_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_org_id", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_index("ix_project_orders_org_id", table_name="project_orders")
    op.drop_index("ix_project_orders_client_id", table_name="project_orders")
    op.drop_table("project_orders")
    op.drop_index("ix_users_org_id", table_name="users")
    op.drop_index("ix_users_client_id", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_clients_org_id", table_name="clients")
    op.drop_table("clients")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
    op.execute("DROP TYPE subscription_status")
    op.execute("DROP TYPE billing_interval")
    op.execute("DROP TYPE order_status")
    op.execute("DROP TYPE user_role")
